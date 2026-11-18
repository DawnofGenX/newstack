use std::io::{self, Read};

use {{ package_name }}::{eval, parse};

const USAGE: &str = "usage: {{ npm_name }} [EXPRESSION]

Reads an s-expression from the argument list or from stdin, evaluates it and
prints the result. Exit status is 1 for a read or evaluation error and 2 for a
bad invocation.";

fn main() -> std::process::ExitCode {
    let mut expression = None;
    for argument in std::env::args().skip(1) {
        match argument.as_str() {
            "-h" | "--help" => {
                println!("{USAGE}");
                return std::process::ExitCode::SUCCESS;
            }
            other if other.starts_with('-') && other != "-" => {
                eprintln!("unknown option: {other}");
                eprintln!("{USAGE}");
                return std::process::ExitCode::from(2);
            }
            other => expression = Some(other.to_string()),
        }
    }
    let source = match expression {
        Some(text) => text,
        None => {
            let mut buffer = String::new();
            if let Err(error) = io::stdin().read_to_string(&mut buffer) {
                eprintln!("cannot read stdin: {error}");
                return std::process::ExitCode::from(1);
            }
            buffer
        }
    };
    if source.trim().is_empty() {
        eprintln!("{USAGE}");
        return std::process::ExitCode::from(2);
    }
    match parse(&source).and_then(|value| eval(&value)) {
        Ok(value) => {
            println!("{value}");
            std::process::ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("{error}");
            std::process::ExitCode::from(1)
        }
    }
}
