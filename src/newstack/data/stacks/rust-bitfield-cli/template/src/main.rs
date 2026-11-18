use std::process::ExitCode;

use clap::Parser;

use {{ package_name }}::{Op, apply, format_result, parse_value};

#[derive(Parser, Debug)]
#[command(name = "{{ npm_name }}", version, about = "bitfield inspector/manipulator")]
struct Cli {
    value: String,
    #[arg(long = "set", value_name = "BIT")]
    set: Vec<u32>,
    #[arg(long = "clear", value_name = "BIT")]
    clear: Vec<u32>,
    #[arg(long = "toggle", value_name = "BIT")]
    toggle: Vec<u32>,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let base = match parse_value(&cli.value) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("error: {e}");
            return ExitCode::FAILURE;
        }
    };
    let mut ops = Vec::new();
    for b in cli.set {
        ops.push(Op::Set(b));
    }
    for b in cli.clear {
        ops.push(Op::Clear(b));
    }
    for b in cli.toggle {
        ops.push(Op::Toggle(b));
    }
    let result = apply(base, &ops);
    println!("{}", format_result(result));
    ExitCode::SUCCESS
}
