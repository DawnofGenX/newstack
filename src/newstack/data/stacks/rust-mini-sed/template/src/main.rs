use std::fs;
use std::io::{self, Read};
use std::process::ExitCode;

use clap::Parser;

use {{ package_name }}::sed;

#[derive(Parser, Debug)]
#[command(
    name = "{{ npm_name }}",
    version,
    about = "minimal sed: s/pattern/replacement/"
)]
struct Cli {
    pattern: String,
    replacement: String,
    file: Option<String>,
    #[arg(short = 'g', long = "global")]
    global: bool,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let mut input = String::new();
    if let Some(path) = &cli.file {
        match fs::read_to_string(path) {
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
    match sed(&input, &cli.pattern, &cli.replacement, cli.global) {
        Ok(out) => {
            print!("{out}");
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("error: {e}");
            ExitCode::FAILURE
        }
    }
}
