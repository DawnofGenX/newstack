import gleam/list
import textstat/options
import textstat/runner

/// Command-line arguments as a list of UTF-8 strings.
@external(erlang, "textstat_io", "args")
fn get_args() -> List(String)

/// All of stdin as a raw byte buffer.
@external(erlang, "textstat_io", "read_stdin")
fn get_stdin() -> BitArray

/// Stop the VM with the given exit code. `gleam run` propagates the VM exit
/// status to the shell, so this is how the CLI sets a real process exit code.
@external(erlang, "erlang", "halt")
fn halt(code: Int) -> Nil

pub fn main() -> Nil {
  let args = get_args()
  let parsed = options.parse(args)
  let needs_stdin =
    list.is_empty(parsed.files) || list.contains(parsed.files, "-")
  let stdin = case needs_stdin {
    True -> get_stdin()
    False -> <<>>
  }
  let code = runner.run(args, stdin)
  halt(code)
}
