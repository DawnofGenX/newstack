use std::process::ExitCode;

use {{ package_name }}::{merge_sorted, parse_block};

fn main() -> ExitCode {
    let paths: Vec<String> = std::env::args().skip(1).collect();
    if paths.is_empty() {
        eprintln!("usage: {{ npm_name }} FILE [FILE ...]");
        return ExitCode::from(2);
    }
    let mut runs = Vec::with_capacity(paths.len());
    for path in &paths {
        let text = match std::fs::read_to_string(path) {
            Ok(text) => text,
            Err(error) => {
                eprintln!("{path}: {error}");
                return ExitCode::FAILURE;
            }
        };
        match parse_block(&text) {
            Ok(values) => runs.push(values),
            Err(message) => {
                eprintln!("{path}: {message}");
                return ExitCode::FAILURE;
            }
        }
    }
    for value in merge_sorted(&runs) {
        println!("{value}");
    }
    ExitCode::SUCCESS
}
