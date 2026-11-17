use std::io::{self, BufRead, Write};
use std::process::ExitCode;

use {{ package_name }}::Dispatcher;

fn main() -> ExitCode {
    let stdin = io::stdin();
    let mut stdin = stdin.lock();
    let stdout = io::stdout();
    let mut stdout = stdout.lock();
    let mut dispatcher = Dispatcher::new();
    let mut line = String::new();

    loop {
        line.clear();
        match stdin.read_line(&mut line) {
            Ok(0) => break,
            Ok(_) => {}
            Err(err) => {
                eprintln!("read error: {err}");
                return ExitCode::FAILURE;
            }
        }

        if let Some(response) = dispatcher.handle_line(&line) {
            // The client is blocked on this line, so a buffered response is a
            // hung client: write it and flush before reading the next request.
            if writeln!(stdout, "{response}").is_err() || stdout.flush().is_err() {
                return ExitCode::FAILURE;
            }
        }
    }

    eprintln!("{} request(s) handled", dispatcher.handled());
    ExitCode::SUCCESS
}
