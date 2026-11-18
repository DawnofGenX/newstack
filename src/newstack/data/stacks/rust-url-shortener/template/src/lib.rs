use std::collections::HashMap;
use std::io::{Read, Write};
use std::net::TcpListener;
use std::net::TcpStream;
use std::sync::{Arc, Mutex};
use std::thread;

#[derive(Default)]
pub struct Store {
    counter: u64,
    map: HashMap<String, String>,
}

impl Store {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, url: String) -> String {
        self.counter += 1;
        let id = base62(self.counter);
        self.map.insert(id.clone(), url);
        id
    }

    pub fn get(&self, id: &str) -> Option<String> {
        self.map.get(id).cloned()
    }
}

pub fn base62(mut n: u64) -> String {
    const ALPHABET: &[u8] = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
    if n == 0 {
        return "0".to_string();
    }
    let mut buf = Vec::new();
    while n > 0 {
        buf.push(ALPHABET[(n % 62) as usize]);
        n /= 62;
    }
    buf.reverse();
    String::from_utf8(buf).unwrap_or_default()
}

pub fn handle_connection(mut stream: TcpStream, store: Arc<Mutex<Store>>) {
    let mut buf = [0u8; 8192];
    let n = stream.read(&mut buf).unwrap_or(0);
    if n == 0 {
        return;
    }
    let req = String::from_utf8_lossy(&buf[..n]);
    let first_line = req.lines().next().unwrap_or("");
    let mut parts = first_line.split_whitespace();
    let method = parts.next().unwrap_or("");
    let path = parts.next().unwrap_or("/");

    if method == "POST" {
        let body = req.split("\r\n\r\n").nth(1).unwrap_or("").trim().to_string();
        let url = if let Some(rest) = body.strip_prefix("url=") {
            percent_decode(rest)
        } else {
            body
        };
        let id = store.lock().unwrap().create(url);
        let resp = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
            id.len(),
            id
        );
        let _ = stream.write_all(resp.as_bytes());
    } else if method == "GET" {
        let id = path.trim_start_matches('/');
        let url = store.lock().unwrap().get(id);
        match url {
            Some(u) => {
                let resp = format!(
                    "HTTP/1.1 302 Found\r\nLocation: {}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n",
                    u
                );
                let _ = stream.write_all(resp.as_bytes());
            }
            None => {
                let _ = stream.write_all(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n");
            }
        }
    } else {
        let _ = stream.write_all(b"HTTP/1.1 405 Method Not Allowed\r\nConnection: close\r\n\r\n");
    }
}

fn percent_decode(s: &str) -> String {
    // minimal: replace + with space; handle %XX
    let mut out = String::new();
    let bytes = s.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 3 <= bytes.len() {
            let hex = &s[i + 1..i + 3];
            if let Ok(v) = u8::from_str_radix(hex, 16) {
                out.push(v as char);
                i += 3;
                continue;
            }
        }
        if bytes[i] == b'+' {
            out.push(' ');
        } else {
            out.push(bytes[i] as char);
        }
        i += 1;
    }
    out
}

pub fn serve(listener: TcpListener, store: Arc<Mutex<Store>>) {
    for s in listener.incoming().flatten() {
        let st = Arc::clone(&store);
        thread::spawn(move || handle_connection(s, st));
    }
}
