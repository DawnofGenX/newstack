use {{ package_name }}::{CliOverrides, parse_dotenv, resolve};
use std::collections::HashMap;
use std::env;
use std::fs;
use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let mut cli = CliOverrides::default();
    let mut command = "print".to_string();
    let mut i = 1;
    if i < args.len() && !args[i].starts_with('-') {
        command = args[i].clone();
        i += 1;
    }
    while i < args.len() {
        match args[i].as_str() {
            "--config" => {
                if i + 1 >= args.len() {
                    eprintln!("missing value for --config");
                    return ExitCode::from(2);
                }
                cli.config = Some(std::path::PathBuf::from(&args[i + 1]));
                i += 2;
            }
            "--env-file" => {
                if i + 1 >= args.len() {
                    eprintln!("missing value for --env-file");
                    return ExitCode::from(2);
                }
                cli.env_file = Some(std::path::PathBuf::from(&args[i + 1]));
                i += 2;
            }
            "--host" => {
                if i + 1 >= args.len() {
                    eprintln!("missing value for --host");
                    return ExitCode::from(2);
                }
                cli.host = Some(args[i + 1].clone());
                i += 2;
            }
            "--port" => {
                if i + 1 >= args.len() {
                    eprintln!("missing value for --port");
                    return ExitCode::from(2);
                }
                cli.port = Some(args[i + 1].clone());
                i += 2;
            }
            "--debug" => {
                cli.debug_set = true;
                i += 1;
            }
            "--name" => {
                if i + 1 >= args.len() {
                    eprintln!("missing value for --name");
                    return ExitCode::from(2);
                }
                cli.name = Some(args[i + 1].clone());
                i += 2;
            }
            "--explain" => {
                cli.explain = true;
                i += 1;
            }
            other => {
                eprintln!("unknown argument: {}", other);
                return ExitCode::from(2);
            }
        }
    }

    if command == "explain" {
        cli.explain = true;
    }

    // Build env map: .env file first, then process env overlays.
    let mut envmap = HashMap::new();
    if let Some(path) = &cli.env_file {
        match fs::read_to_string(path) {
            Ok(text) => {
                for (k, v) in parse_dotenv(&text) {
                    envmap.insert(k, v);
                }
            }
            Err(e) => {
                eprintln!("{}", e);
                return ExitCode::from(1);
            }
        }
    }
    for (k, v) in env::vars() {
        envmap.insert(k, v);
    }

    match resolve(&cli, &envmap) {
        Ok(layers) => {
            if cli.explain || command == "explain" {
                for (key, layer) in &layers.provenance {
                    let val = match key.as_str() {
                        "host" => layers.config.host.clone(),
                        "port" => layers.config.port.to_string(),
                        "debug" => layers.config.debug.to_string(),
                        "name" => layers.config.name.clone(),
                        _ => String::new(),
                    };
                    println!("{} = {} ({})", key, val, layer);
                }
            } else {
                match serde_json::to_string_pretty(&layers.config) {
                    Ok(s) => println!("{}", s),
                    Err(e) => {
                        eprintln!("{}", e);
                        return ExitCode::from(1);
                    }
                }
            }
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("{}", e);
            ExitCode::from(1)
        }
    }
}
