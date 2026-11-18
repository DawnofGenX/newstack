use std::io::Read;
use std::process::ExitCode;

use {{ package_name }}::{candidates, count_solutions, format, is_complete, is_valid, parse, solve};

const USAGE: &str = "usage: sudoku-solver [--grid TEXT | FILE] [--candidates N] [--count]

Reads a puzzle of 81 digits (0 or . for empty, whitespace ignored) from --grid,
a file argument or standard input and prints the solution.

  --grid TEXT      the puzzle on the command line
  --candidates N   list the digits that can go into cell N (0 based)
  --count          print the number of solutions, capped at 2
  -h, --help       print this message

Exit status is 0 when the puzzle is solved, 1 when it is invalid or has no
solution and 2 for bad usage.";

fn main() -> ExitCode {
    match run(std::env::args().skip(1).collect()) {
        Ok(code) => code,
        Err(Failure::Usage(message)) => {
            eprintln!("error: {message}");
            eprintln!("{USAGE}");
            ExitCode::from(2)
        }
        Err(Failure::Input(message)) => {
            eprintln!("error: {message}");
            ExitCode::from(1)
        }
    }
}

enum Failure {
    Usage(String),
    Input(String),
}

fn run(arguments: Vec<String>) -> Result<ExitCode, Failure> {
    let mut puzzle: Option<String> = None;
    let mut candidate_index: Option<usize> = None;
    let mut count = false;
    let mut index = 0;

    while index < arguments.len() {
        let argument = arguments[index].as_str();
        match argument {
            "-h" | "--help" => {
                println!("{USAGE}");
                return Ok(ExitCode::SUCCESS);
            }
            "--count" => count = true,
            "--grid" | "--candidates" => {
                index += 1;
                let Some(value) = arguments.get(index) else {
                    return Err(Failure::Usage(format!("{argument} needs a value")));
                };
                if argument == "--grid" {
                    puzzle = Some(value.clone());
                } else {
                    let parsed = value
                        .parse::<usize>()
                        .map_err(|_| Failure::Usage(format!("not a cell index: {value}")))?;
                    candidate_index = Some(parsed);
                }
            }
            other if other.starts_with('-') && other != "-" => {
                return Err(Failure::Usage(format!("unknown option {other}")));
            }
            other => {
                if puzzle.is_some() {
                    return Err(Failure::Usage("only one puzzle may be given".into()));
                }
                puzzle = Some(read_file(other)?);
            }
        }
        index += 1;
    }

    let text = match puzzle {
        Some(text) => text,
        None => {
            let mut buffer = String::new();
            std::io::stdin()
                .read_to_string(&mut buffer)
                .map_err(|error| Failure::Input(format!("cannot read stdin: {error}")))?;
            buffer
        }
    };

    let grid = parse(&text).map_err(|error| Failure::Input(error.to_string()))?;

    if let Some(cell) = candidate_index {
        if cell >= grid.len() {
            return Err(Failure::Usage(format!(
                "cell {cell} is outside 0..{}",
                grid.len()
            )));
        }
        let options = candidates(&grid, cell);
        let rendered: Vec<String> = options.iter().map(|digit| digit.to_string()).collect();
        println!("{}", rendered.join(" "));
        return Ok(ExitCode::SUCCESS);
    }

    if count {
        println!("{}", count_solutions(&grid, 2));
        return Ok(ExitCode::SUCCESS);
    }

    if !is_valid(&grid) {
        return Err(Failure::Input("the puzzle breaks Sudoku rules".into()));
    }
    match solve(&grid) {
        Some(solution) => {
            debug_assert!(is_complete(&solution));
            println!("{}", format(&solution));
            Ok(ExitCode::SUCCESS)
        }
        None => Err(Failure::Input("the puzzle has no solution".into())),
    }
}

fn read_file(path: &str) -> Result<String, Failure> {
    std::fs::read_to_string(path)
        .map_err(|error| Failure::Input(format!("cannot read {path}: {error}")))
}
