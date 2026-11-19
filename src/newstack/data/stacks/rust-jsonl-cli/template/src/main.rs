use std::env;
use std::fs::File;
use std::io::BufReader;
use std::process::ExitCode;

use {{ package_name }}::query_jsonl;

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let mut file: Option<String> = None;
    let mut select: Option<String> = None;
    let mut where_field: Option<String> = None;
    let mut where_value: Option<String> = None;
    let mut count_only = false;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "-file" => {
                file = Some(args[i + 1].clone());
                i += 2;
            }
            "-select" => {
                select = Some(args[i + 1].clone());
                i += 2;
            }
            "-where" => {
                let cond = args[i + 1].clone();
                if let Some(pos) = cond.find("==") {
                    where_field = Some(cond[..pos].to_string());
                    where_value = Some(cond[pos + 2..].to_string());
                }
                i += 2;
            }
            "-count" => {
                count_only = true;
                i += 1;
            }
            "-h" | "--help" => {
                println!("usage: jsonlq -file F [-select field] [-where field==value] [-count]");
                return ExitCode::SUCCESS;
            }
            _ => {
                i += 1;
            }
        }
    }

    let reader: Box<dyn std::io::BufRead> = match file {
        Some(p) => match File::open(&p) {
            Ok(f) => Box::new(BufReader::new(f)),
            Err(e) => {
                eprintln!("error: {e}");
                return ExitCode::FAILURE;
            }
        },
        None => Box::new(BufReader::new(std::io::stdin())),
    };

    let (out, total) = query_jsonl(
        reader,
        select.as_deref(),
        where_field.as_deref(),
        where_value.as_deref(),
        count_only,
    );
    if count_only {
        println!("{}", total);
    } else {
        for v in out {
            println!("{}", v);
        }
    }
    ExitCode::SUCCESS
}
