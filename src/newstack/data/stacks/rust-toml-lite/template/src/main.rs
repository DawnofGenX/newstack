use std::env;
use std::fs;
use std::io::{self, Read};

use {{ package_name }}::parse;

fn read_input() -> Result<String, String> {
    let args: Vec<String> = env::args().collect();
    if args.len() <= 1 {
        let mut buf = String::new();
        io::stdin()
            .read_to_string(&mut buf)
            .map_err(|e| e.to_string())?;
        return Ok(buf);
    }
    let path = &args[1];
    if path == "-" {
        let mut buf = String::new();
        io::stdin()
            .read_to_string(&mut buf)
            .map_err(|e| e.to_string())?;
        Ok(buf)
    } else {
        fs::read_to_string(path).map_err(|e| e.to_string())
    }
}

fn main() {
    match read_input() {
        Ok(input) => match parse(&input) {
            Ok(v) => println!("{}", v.to_json()),
            Err(e) => {
                eprintln!("error: {}", e);
                std::process::exit(1);
            }
        },
        Err(e) => {
            eprintln!("error: {}", e);
            std::process::exit(1);
        }
    }
}
