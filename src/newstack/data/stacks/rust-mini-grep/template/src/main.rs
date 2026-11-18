use std::path::PathBuf;
use std::process::ExitCode;

use clap::Parser;

use {{ package_name }}::{Options, search_dir};

#[derive(Parser, Debug)]
#[command(name = "{{ npm_name }}", version, about = "recursive regex grep")]
struct Cli {
    pattern: String,
    path: PathBuf,
    #[arg(short = 'i')]
    ignore_case: bool,
    #[arg(short = 'n')]
    line_number: bool,
    #[arg(short = 'c')]
    count: bool,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let options = Options {
        ignore_case: cli.ignore_case,
        line_number: cli.line_number,
        count_only: cli.count,
    };
    match search_dir(&cli.path, &cli.pattern, options) {
        Ok(matches) => {
            if cli.count {
                println!("{}", matches.len());
            } else {
                for m in matches {
                    if cli.line_number {
                        println!("{}:{}:{}", m.path, m.line_number, m.line);
                    } else {
                        println!("{}:{}", m.path, m.line);
                    }
                }
            }
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("error: {e}");
            ExitCode::FAILURE
        }
    }
}
