use std::io::{Read, Write};
use std::net::TcpListener;
use std::thread;
use std::time::Duration;

use {{ package_name }}::{serve, Store};
use std::sync::{Arc, Mutex};

#[test]
fn create_and_redirect() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let store = Arc::new(Mutex::new(Store::new()));
    let s = Arc::clone(&store);
    thread::spawn(move || serve(listener, s));
    thread::sleep(Duration::from_millis(100));

    let mut stream = std::net::TcpStream::connect(format!("127.0.0.1:{}", port)).unwrap();
    let body = "https://example.com/hello";
    let req = format!(
        "POST / HTTP/1.1\r\nHost: x\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        body.len(),
        body
    );
    stream.write_all(req.as_bytes()).unwrap();
    let mut resp = String::new();
    stream.read_to_string(&mut resp).unwrap();
    let id = resp.split("\r\n\r\n").nth(1).unwrap_or("").trim().to_string();
    assert!(!id.is_empty());

    let mut stream = std::net::TcpStream::connect(format!("127.0.0.1:{}", port)).unwrap();
    let req = format!("GET /{} HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n", id);
    stream.write_all(req.as_bytes()).unwrap();
    let mut resp = String::new();
    stream.read_to_string(&mut resp).unwrap();
    assert!(resp.contains("302"), "{}", resp);
    assert!(resp.contains("Location: https://example.com/hello"), "{}", resp);
}

#[test]
fn unknown_returns_404() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let store = Arc::new(Mutex::new(Store::new()));
    let s = Arc::clone(&store);
    thread::spawn(move || serve(listener, s));
    thread::sleep(Duration::from_millis(100));

    let mut stream = std::net::TcpStream::connect(format!("127.0.0.1:{}", port)).unwrap();
    let req = "GET /nope HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n";
    stream.write_all(req.as_bytes()).unwrap();
    let mut resp = String::new();
    stream.read_to_string(&mut resp).unwrap();
    assert!(resp.contains("404"), "{}", resp);
}
