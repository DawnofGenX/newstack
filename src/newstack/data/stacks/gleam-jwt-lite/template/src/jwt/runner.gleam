import gleam/io
import gleam/option
import jwt/options
import jwt/token

const program = "{{ npm_name }}"

/// Run with parsed arguments, returning the process exit code.
pub fn run(args: List(String)) -> Int {
  case options.parse(args) {
    options.Parsed(options.Help, _) -> {
      io.println(usage())
      0
    }
    options.Parsed(options.Version, _) -> {
      io.println("0.1.0")
      0
    }
    options.Parsed(options.UsageError(message), _) -> {
      io.println_error("error: " <> message)
      io.println_error(usage())
      2
    }
    options.Parsed(options.Ok, option.Some(command)) -> run_command(command)
    options.Parsed(options.Ok, option.None) -> {
      io.println_error("error: missing command")
      2
    }
  }
}

fn run_command(command: options.Command) -> Int {
  case command {
    options.Sign(secret, payload) -> {
      io.println(token.sign(secret, token.default_header, payload))
      0
    }
    options.Verify(secret, encoded) -> {
      case token.verify(secret, encoded) {
        Ok(payload) -> {
          io.println(payload)
          0
        }
        Error(reason) -> {
          io.println_error("error: " <> reason)
          1
        }
      }
    }
    options.Claims(claims) -> {
      io.println(token.encode_claims(claims))
      0
    }
  }
}

fn usage() -> String {
  "Usage: "
  <> program
  <> " [--help|--version] sign SECRET PAYLOAD_JSON | verify SECRET TOKEN | claims KEY=VALUE..."
}
