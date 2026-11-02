//! Core logic for {{ title }}.
//!
//! The crate is split into a library so the argument parsing and the greeting
//! formatting can be tested without spawning a process.

/// Name used when the caller does not pass `--name`.
pub const DEFAULT_NAME: &str = "world";

/// Version reported by `--version`, taken from `Cargo.toml`.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Usage line printed alongside a parse error.
pub const USAGE: &str = "usage: {{ npm_name }} greet [--name <name>] | --version";

const NAME_FLAG: &str = "--name";
const NAME_FLAG_EQ: &str = "--name=";

/// A command line parsed from the process arguments.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Command {
    /// Print a greeting for the given name.
    Greet(String),
    /// Print the program version.
    Version,
}

/// Build the greeting printed by [`Command::Greet`].
pub fn greet(name: &str) -> String {
    format!("Hello, {name}!")
}

/// Parse the arguments that follow the program name.
///
/// Accepts `greet` (optional), `--name <value>` or `--name=<value>`, and
/// `--version`. No arguments at all is equivalent to `greet` with
/// [`DEFAULT_NAME`].
pub fn parse<I: Iterator<Item = String>>(args: I) -> Result<Command, String> {
    let mut name = DEFAULT_NAME.to_string();
    let mut saw_greet = false;
    let mut args = args.into_iter();

    while let Some(arg) = args.next() {
        match arg.as_str() {
            "greet" => {
                if saw_greet {
                    return Err(format!("unexpected argument: {arg}\n{USAGE}"));
                }
                saw_greet = true;
            }
            "--version" | "-V" => return Ok(Command::Version),
            NAME_FLAG => {
                let value = args
                    .next()
                    .ok_or_else(|| format!("{NAME_FLAG} requires a value\n{USAGE}"))?;
                name = value;
            }
            other if other.starts_with(NAME_FLAG_EQ) => {
                name = other[NAME_FLAG_EQ.len()..].to_string();
            }
            other => return Err(format!("unrecognized argument: {other}\n{USAGE}")),
        }
    }

    if name.trim().is_empty() {
        return Err(format!("name must not be empty\n{USAGE}"));
    }

    Ok(Command::Greet(name))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn parse_args(args: &[&str]) -> Result<Command, String> {
        parse(args.iter().map(|arg| arg.to_string()))
    }

    #[test]
    fn no_arguments_greets_the_default_name() {
        assert_eq!(
            parse_args(&[]),
            Ok(Command::Greet(DEFAULT_NAME.to_string()))
        );
        assert_eq!(greet(DEFAULT_NAME), "Hello, world!");
    }

    #[test]
    fn named_greet_is_parsed() {
        assert_eq!(
            parse_args(&["greet", "--name", "you"]),
            Ok(Command::Greet("you".to_string()))
        );
    }

    #[test]
    fn equals_form_is_parsed() {
        assert_eq!(
            parse_args(&["--name=you"]),
            Ok(Command::Greet("you".to_string()))
        );
    }

    #[test]
    fn version_flag_is_parsed() {
        assert_eq!(parse_args(&["--version"]), Ok(Command::Version));
    }

    #[test]
    fn unknown_flag_is_an_error() {
        let err = parse_args(&["--nope"]).expect_err("unknown flag must fail");
        assert!(err.contains("--nope"), "error should name the flag: {err}");
        assert!(err.contains("usage:"), "error should show usage: {err}");
    }

    #[test]
    fn missing_name_value_is_an_error() {
        assert!(parse_args(&["greet", "--name"]).is_err());
    }
}
