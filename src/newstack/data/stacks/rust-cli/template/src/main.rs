use std::process::ExitCode;

use {{ package_name }}::{Command, VERSION, greet, parse};

fn main() -> ExitCode {
    match parse(std::env::args().skip(1)) {
        Ok(Command::Greet(name)) => {
            println!("{}", greet(&name));
            ExitCode::SUCCESS
        }
        Ok(Command::Version) => {
            println!("{VERSION}");
            ExitCode::SUCCESS
        }
        Err(message) => {
            eprintln!("error: {message}");
            ExitCode::from(2)
        }
    }
}
