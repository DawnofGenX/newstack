use std::io::{self, Read};
use std::process::ExitCode;

use clap::Parser;

use {{ package_name }}::csv_to_json;

#[derive(Parser, Debug)]
#[command(name = "{{ npm_name }}", version, about = "convert CSV to JSON")]
struct Cli {
    /// Input CSV file (reads stdin if omitted)
    input: Option<String>,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let mut input = String::new();
    if let Some(path) = cli.input {
        match std::fs::read_to_string(&path) {
            Ok(s) => input = s,
            Err(e) => {
                eprintln!("error: {e}");
                return ExitCode::FAILURE;
            }
        }
    } else {
        if let Err(e) = io::stdin().read_to_string(&mut input) {
            eprintln!("error: {e}");
            return ExitCode::FAILURE;
        }
    }
    match csv_to_json(&input) {
        Ok(out) => {
            println!("{out}");
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("error: {e}");
            ExitCode::FAILURE
        }
    }
}
