import gleam/dynamic
import gleam/int
import gleam/io
import gleam/list
import gleam/string
import textstat/counts
import textstat/options

/// The program name, used in the usage line.
const program = "{{ npm_name }}"

/// Read a file's contents as a raw byte buffer. `file:read_file` returns
/// `{ok, Binary}` or `{error, Reason}`; the reason is an arbitrary Erlang term
/// so it is typed as `dynamic.Dynamic`.
@external(erlang, "file", "read_file")
fn read_file(path: String) -> Result(BitArray, dynamic.Dynamic)

/// Run the program with the given args and stdin, returning the exit code.
///
/// This is the exit-code contract:
/// - 0: success, including `--help` and `--version`
/// - 1: a file could not be read (other files are still counted)
/// - 2: usage error (unknown flag)
pub fn run(args: List(String), stdin: BitArray) -> Int {
  let parsed = options.parse(args)
  case parsed.status {
    options.Help -> {
      io.println(usage())
      0
    }
    options.Version -> {
      io.println("0.1.0")
      0
    }
    options.UsageError(message) -> {
      io.println_error("error: " <> message)
      io.println_error("")
      io.println_error(usage())
      2
    }
    options.Ok -> {
      // No FILE means stdin, like `wc`: an empty file list is a list of one
      // stdin entry, not a list of zero rows.
      let files = case parsed.files {
        [] -> ["-"]
        files -> files
      }
      run_ok(parsed.figures, files, stdin)
    }
  }
}

fn run_ok(
  figures: options.Figures,
  files: List(String),
  stdin: BitArray,
) -> Int {
  let entries =
    list.map(files, fn(f) {
      case f {
        "" | "-" -> Ok(#(f, counts.of_bytes(stdin)))
        path ->
          case read_file(path) {
            Ok(data) -> Ok(#(path, counts.of_bytes(data)))
            Error(_) -> Error(path)
          }
      }
    })
  let #(total_counts, any_failed) =
    list.fold(entries, #(counts.zero(), False), fn(acc, entry) {
      let #(acc_total, acc_failed) = acc
      case entry {
        Ok(#(path, c)) -> {
          print_row(figures, c, path)
          #(counts.add(acc_total, c), acc_failed)
        }
        Error(path) -> {
          io.println_error("error: cannot open '" <> path <> "'")
          #(acc_total, True)
        }
      }
    })
  case list.length(files) > 1 {
    True -> print_row(figures, total_counts, "total")
    False -> Nil
  }
  case any_failed {
    True -> 1
    False -> 0
  }
}

/// Print one row of figures, right-aligned to the width of the widest figure
/// (the `wc` column layout), followed by the path.
fn print_row(figures: options.Figures, c: counts.Counts, path: String) -> Nil {
  let values =
    list.append(
      list.append(
        case figures.lines {
          True -> [c.lines]
          False -> []
        },
        case figures.words {
          True -> [c.words]
          False -> []
        },
      ),
      case figures.bytes {
        True -> [c.bytes]
        False -> []
      },
    )
  let width = list.fold(values, 1, fn(acc, v) { int.max(acc, int_length(v)) })
  let figs_str =
    list.map(values, fn(v) { right_align(int.to_string(v), width) })
  let joined = string.join(figs_str, " ")
  let line = case path {
    "" | "-" -> joined
    p -> joined <> " " <> p
  }
  io.println(line)
}

/// The number of decimal digits in a non-negative integer.
fn int_length(n: Int) -> Int {
  int_length_helper(n, 1)
}

fn int_length_helper(n: Int, acc: Int) -> Int {
  case n < 10 {
    True -> acc
    False -> int_length_helper(n / 10, acc + 1)
  }
}

/// Right-align a string to the given width, padding with spaces.
fn right_align(s: String, width: Int) -> String {
  let len = string.length(s)
  case len >= width {
    True -> s
    False -> string.repeat(" ", width - len) <> s
  }
}

/// The usage text, printed by `--help` and on a usage error.
fn usage() -> String {
  "Usage: "
  <> program
  <> " [OPTION]... [FILE]...\n"
  <> "\n"
  <> "Count lines, words and bytes in each FILE, or from stdin with no FILE.\n"
  <> "\n"
  <> "  -l, --lines     print the line counts\n"
  <> "  -w, --words     print the word counts\n"
  <> "  -c, --bytes     print the byte counts\n"
  <> "  -h, --help      print this help and exit\n"
  <> "  -V, --version   print the version and exit\n"
  <> "\n"
  <> "With no counting flag, all three figures are printed. With more than\n"
  <> "one FILE a total line is printed. A missing or unreadable FILE is an\n"
  <> "error (exit 1); an unknown option is a usage error (exit 2).\n"
}
