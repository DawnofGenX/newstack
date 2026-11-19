import gleam/list
import gleam/option
import gleam/string

pub type Status {
  Ok
  Help
  Version
  UsageError(String)
}

pub type Command {
  Sign(secret: String, payload: String)
  Verify(secret: String, token: String)
  Claims(List(#(String, String)))
}

pub type Parsed {
  Parsed(status: Status, command: option.Option(Command))
}

/// Hand-written argument parser: `gleam run` hands us the words after `--`.
pub fn parse(args: List(String)) -> Parsed {
  case args {
    [] -> Parsed(UsageError("expected a command"), option.None)
    ["--help", ..] | ["-h", ..] -> Parsed(Help, option.None)
    ["--version", ..] -> Parsed(Version, option.None)
    ["sign", secret, payload] -> Parsed(Ok, option.Some(Sign(secret, payload)))
    ["verify", secret, token] -> Parsed(Ok, option.Some(Verify(secret, token)))
    ["claims", ..rest] -> parse_claims(rest, [])
    [unknown, ..] ->
      Parsed(UsageError("unknown command: " <> unknown), option.None)
  }
}

fn parse_claims(items: List(String), acc: List(#(String, String))) -> Parsed {
  case items {
    [] -> Parsed(Ok, option.Some(Claims(list.reverse(acc))))
    [item, ..rest] ->
      case string.split(item, "=") {
        [key, value] -> parse_claims(rest, [#(key, value), ..acc])
        [key, value, ..] -> parse_claims(rest, [#(key, value), ..acc])
        _ -> Parsed(UsageError("expected KEY=VALUE claim"), option.None)
      }
  }
}
