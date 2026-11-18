use std::process::ExitCode;

use clap::{Parser, Subcommand};

use {{ package_name }}::{bump, compare, parse};

#[derive(Parser, Debug)]
#[command(name = "{{ npm_name }}", version, about = "semver parse/compare/bump")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand, Debug)]
enum Command {
    Parse { version: String },
    Compare { a: String, b: String },
    Bump { version: String, level: String },
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    match cli.command {
        Command::Parse { version } => match parse(&version) {
            Ok(v) => {
                println!("{v}");
                ExitCode::SUCCESS
            }
            Err(e) => {
                eprintln!("error: {e}");
                ExitCode::FAILURE
            }
        },
        Command::Compare { a, b } => match compare(&a, &b) {
            Ok(n) => {
                println!("{n}");
                ExitCode::SUCCESS
            }
            Err(e) => {
                eprintln!("error: {e}");
                ExitCode::FAILURE
            }
        },
        Command::Bump { version, level } => match bump(&version, &level) {
            Ok(v) => {
                println!("{v}");
                ExitCode::SUCCESS
            }
            Err(e) => {
                eprintln!("error: {e}");
                ExitCode::FAILURE
            }
        },
    }
}
