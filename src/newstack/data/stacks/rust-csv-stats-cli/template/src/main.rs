use std::env;
use std::path::PathBuf;
use std::process::ExitCode;

use {{ package_name }}::analyze_path;

fn main() -> ExitCode {
    let mut args = env::args().skip(1);
    let Some(input) = args.next() else {
        eprintln!("usage: {{ npm_name }} <input.csv>");
        return ExitCode::FAILURE;
    };

    match analyze_path(PathBuf::from(input).as_path()) {
        Ok(stats) => {
            for stat in stats {
                println!(
                    "{} count={} min={} max={} mean={} unique={}",
                    stat.name,
                    stat.count,
                    stat.min
                        .map(|value| value.to_string())
                        .unwrap_or_else(|| "-".to_owned()),
                    stat.max
                        .map(|value| value.to_string())
                        .unwrap_or_else(|| "-".to_owned()),
                    stat.mean
                        .map(|value| value.to_string())
                        .unwrap_or_else(|| "-".to_owned()),
                    stat.unique
                );
            }
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("error: {error}");
            ExitCode::FAILURE
        }
    }
}
