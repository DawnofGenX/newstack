use std::io::{self, Read, Write};
use std::process::exit;

use {{ package_name }}::{decode, encode};

fn read_input(file: Option<&str>) -> Vec<u8> {
    match file {
        Some("-") | None => {
            let mut buf = Vec::new();
            if io::stdin().read_to_end(&mut buf).is_err() {
                eprintln!("failed to read stdin");
                exit(1);
            }
            buf
        }
        Some(path) => match std::fs::read(path) {
            Ok(b) => b,
            Err(e) => {
                eprintln!("cannot read {}: {}", path, e);
                exit(1);
            }
        },
    }
}

fn main() {
    let args = std::env::args().skip(1);
    let mut decode_mode = false;
    let mut url_safe = false;
    let mut pad = true;
    let mut file: Option<String> = None;

    for a in args {
        match a.as_str() {
            "-d" | "--decode" => decode_mode = true,
            "--url-safe" => url_safe = true,
            "--no-pad" => pad = false,
            "-h" | "--help" => {
                println!("Usage: b64 [-d] [--url-safe] [--no-pad] [FILE]");
                exit(0);
            }
            s if s.starts_with("--") => {
                eprintln!("unknown option: {}", s);
                exit(2);
            }
            s if s.starts_with('-') && s.len() > 1 => {
                // support combined short? minimal
                eprintln!("unknown option: {}", s);
                exit(2);
            }
            other => {
                if file.is_some() {
                    eprintln!("unexpected argument: {}", other);
                    exit(2);
                }
                file = Some(other.to_string());
            }
        }
    }

    let data = read_input(file.as_deref());

    if decode_mode {
        let text = String::from_utf8_lossy(&data);
        match decode(&text, url_safe) {
            Ok(bytes) => {
                let _ = io::stdout().write_all(&bytes);
            }
            Err(e) => {
                eprintln!("decode error: {}", e);
                exit(1);
            }
        }
    } else {
        let out = encode(&data, url_safe, pad);
        println!("{}", out);
    }
}
