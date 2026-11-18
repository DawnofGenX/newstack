use std::env;
use std::fs;
use std::io::{self, Read};
use std::process::ExitCode;

use {{ package_name }}::{crc32, crc32c, to_hex};

fn read_input(path: &str) -> Result<Vec<u8>, String> {
    if path == "-" {
        let mut buffer = Vec::new();
        io::stdin()
            .read_to_end(&mut buffer)
            .map_err(|error| format!("cannot read stdin: {error}"))?;
        return Ok(buffer);
    }
    fs::read(path).map_err(|error| format!("cannot read {path}: {error}"))
}

fn main() -> ExitCode {
    let mut castagnoli = false;
    let mut paths: Vec<String> = Vec::new();
    for argument in env::args().skip(1) {
        match argument.as_str() {
            "--crc32c" | "-c" => castagnoli = true,
            "--help" | "-h" => {
                println!("usage: {{ npm_name }} [--crc32c] [FILE ...]");
                println!(
                    "computes a CRC-32 checksum of each file, or of stdin when no file is given"
                );
                return ExitCode::SUCCESS;
            }
            other if other.starts_with('-') && other != "-" => {
                eprintln!("unknown option: {other}");
                return ExitCode::from(2);
            }
            other => paths.push(other.to_string()),
        }
    }
    if paths.is_empty() {
        paths.push(String::from("-"));
    }

    for path in paths {
        let bytes = match read_input(&path) {
            Ok(bytes) => bytes,
            Err(message) => {
                eprintln!("{message}");
                return ExitCode::from(1);
            }
        };
        let sum = if castagnoli {
            crc32c(&bytes)
        } else {
            crc32(&bytes)
        };
        if path == "-" {
            println!("{}", to_hex(sum));
        } else {
            println!("{} {path}", to_hex(sum));
        }
    }
    ExitCode::SUCCESS
}
