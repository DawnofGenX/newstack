import gleam/bit_array
import gleam/io
import json_parser as json

@external(erlang, "json_io", "args")
fn get_args() -> List(String)

@external(erlang, "json_io", "read_stdin")
fn get_stdin() -> BitArray

@external(erlang, "erlang", "halt")
fn halt(code: Int) -> Nil

pub fn main() -> Nil {
  let args = get_args()
  let input = case bit_array.to_string(get_stdin()) {
    Ok(s) -> s
    Error(_) -> ""
  }
  case args {
    [] -> run_compact(input)
    ["compact"] -> run_compact(input)
    ["-c"] -> run_compact(input)
    ["pretty"] -> run_pretty(input)
    ["-p"] -> run_pretty(input)
    ["--pretty"] -> run_pretty(input)
    ["--help"] -> {
      io.println("Usage: json-cli [compact|pretty]")
      halt(0)
    }
    ["-h"] -> {
      io.println("Usage: json-cli [compact|pretty]")
      halt(0)
    }
    _ -> {
      io.println("json-cli: unknown option")
      halt(2)
    }
  }
}

fn run_compact(input: String) -> Nil {
  case json.to_compact(input) {
    Ok(out) -> { io.print(out) halt(0) }
    Error(e) -> { io.println("json: " <> e) halt(1) }
  }
}

fn run_pretty(input: String) -> Nil {
  case json.to_pretty(input) {
    Ok(out) -> { io.println(out) halt(0) }
    Error(e) -> { io.println("json: " <> e) halt(1) }
  }
}