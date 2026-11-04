import gleam/list
import gleam/string

/// Which figures to print. With no counting flag given, all three are set.
pub type Figures {
  Figures(lines: Bool, words: Bool, bytes: Bool)
}

/// The parse status of the command line.
pub type Status {
  Ok
  Help
  Version
  UsageError(message: String)
}

/// The parsed command line: which figures to print, which files to read, and
/// the status (Ok, Help, Version or UsageError).
pub type Parsed {
  Parsed(figures: Figures, files: List(String), status: Status)
}

/// Parse a command line into figures, files and a status.
///
/// `""` and `"-"` name stdin. `--` ends option parsing. `-h`/`--help` and
/// `-V`/`--version` are recognised. `-l`/`--lines`, `-w`/`--words` and
/// `-c`/`--bytes` select individual figures. Any other leading-dash argument
/// is a usage error. With no counting flag, all three figures are printed.
pub fn parse(args: List(String)) -> Parsed {
  parse_helper(
    args,
    Figures(lines: False, words: False, bytes: False),
    [],
    True,
  )
}

fn parse_helper(
  args: List(String),
  figures: Figures,
  files: List(String),
  in_options: Bool,
) -> Parsed {
  case args {
    [] -> Parsed(figures: default_figures(figures), files: files, status: Ok)
    [arg, ..rest] -> {
      let is_option = in_options && string.starts_with(arg, "-") && arg != "-"
      case is_option {
        False ->
          // A file (or "-" for stdin).
          parse_helper(rest, figures, list.append(files, [arg]), in_options)
        True ->
          case arg {
            "--" ->
              Parsed(
                figures: default_figures(figures),
                files: list.append(files, rest),
                status: Ok,
              )
            "-h" | "--help" ->
              Parsed(figures: figures, files: files, status: Help)
            "-V" | "--version" ->
              Parsed(figures: figures, files: files, status: Version)
            "-l" | "--lines" ->
              parse_helper(rest, Figures(..figures, lines: True), files, True)
            "-w" | "--words" ->
              parse_helper(rest, Figures(..figures, words: True), files, True)
            "-c" | "--bytes" ->
              parse_helper(rest, Figures(..figures, bytes: True), files, True)
            _ ->
              Parsed(
                figures: figures,
                files: files,
                status: UsageError("unknown option '" <> arg <> "'"),
              )
          }
      }
    }
  }
}

/// With no counting flag given, print all three figures (the `wc` default).
fn default_figures(figures: Figures) -> Figures {
  case figures.lines || figures.words || figures.bytes {
    True -> figures
    False -> Figures(lines: True, words: True, bytes: True)
  }
}
