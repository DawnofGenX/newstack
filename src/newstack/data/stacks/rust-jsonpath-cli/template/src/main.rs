use std::fs;
use std::io::{self, Read};
use std::process::ExitCode;

use clap::Parser;
use serde_json::Value;

use {{ package_name }}::eval_path;

#[derive(Parser, Debug)]
#[command(name = "{{ npm_name }}", version, about = "evaluate a JSONPath expression")]
struct Cli {
    /// Input file (reads stdin if omitted) followed by JSONPath expression
    #[arg(num_args = 1..=2, value_names = ["FILE", "EXPR"])]
    args: Vec<String>,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let (file, expr) = match cli.args.as_slice() {
        [expr] => (None, expr.to_string()),
        [file, expr] => (Some(file.to_string()), expr.to_string()),
        _ => {
            eprintln!("usage: {{ npm_name }} [file] <expr>");
            return ExitCode::FAILURE;
        }
    };
    let text = match file {
        Some(p) => match fs::read_to_string(&p) {
            Ok(t) => t,
            Err(e) => {
                eprintln!("error: {e}");
                return ExitCode::FAILURE;
            }
        },
        None => {
            let mut buf = String::new();
            if let Err(e) = io::stdin().read_to_string(&mut buf) {
                eprintln!("error: {e}");
                return ExitCode::FAILURE;
            }
            buf
        }
    };
    let root: Value = match serde_json::from_str(&text) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("error: {e}");
            return ExitCode::FAILURE;
        }
    };
    match eval_path(&root, &expr) {
        Ok(v) => {
            println!("{}", serde_json::to_string(&v).unwrap());
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("error: {e}");
            ExitCode::FAILURE
        }
    }
}
