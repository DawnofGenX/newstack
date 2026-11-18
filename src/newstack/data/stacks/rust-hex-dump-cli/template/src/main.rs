use std::fs;
use std::io::{self, Read};
use std::process::ExitCode;

use clap::Parser;

use {{ package_name }}::hex_dump;

#[derive(Parser, Debug)]
#[command(name = "{{ npm_name }}", version, about = "hex dump of a file or stdin")]
struct Cli {
    /// Input file (reads stdin if omitted)
    file: Option<String>,
    /// Bytes per line
    #[arg(short = 'w', long = "width", default_value_t = 16)]
    width: usize,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let data = match &cli.file {
        Some(p) => match fs::read(p) {
            Ok(d) => d,
            Err(e) => {
                eprintln!("error: {e}");
                return ExitCode::FAILURE;
            }
        },
        None => {
            let mut buf = Vec::new();
            if let Err(e) = io::stdin().read_to_end(&mut buf) {
                eprintln!("error: {e}");
                return ExitCode::FAILURE;
            }
            buf
        }
    };
    print!("{}", hex_dump(&data, cli.width));
    ExitCode::SUCCESS
}
