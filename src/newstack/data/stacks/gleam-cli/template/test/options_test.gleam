import harness
import textstat/options

/// Run the options tests. Returns a list of failed check names (empty if all
/// pass).
pub fn run() -> List(String) {
  [
    // No args: all figures, no files, Ok.
    harness.check("no-args status ok", options.parse([]).status == options.Ok),
    harness.check(
      "no-args all figures",
      options.parse([]).figures
        == options.Figures(lines: True, words: True, bytes: True),
    ),
    harness.check("no-args no files", options.parse([]).files == []),
    // -l: lines only.
    harness.check(
      "-l figures",
      options.parse(["-l"]).figures
        == options.Figures(lines: True, words: False, bytes: False),
    ),
    // -w: words only.
    harness.check(
      "-w figures",
      options.parse(["-w"]).figures
        == options.Figures(lines: False, words: True, bytes: False),
    ),
    // -c: bytes only.
    harness.check(
      "-c figures",
      options.parse(["-c"]).figures
        == options.Figures(lines: False, words: False, bytes: True),
    ),
    // Combined flags.
    harness.check(
      "-l -w figures",
      options.parse(["-l", "-w"]).figures
        == options.Figures(lines: True, words: True, bytes: False),
    ),
    // Long flags.
    harness.check(
      "--lines figures",
      options.parse(["--lines"]).figures
        == options.Figures(lines: True, words: False, bytes: False),
    ),
    // Files.
    harness.check("file parsed", options.parse(["a.txt"]).files == ["a.txt"]),
    // "-" is stdin (a file).
    harness.check("dash is stdin", options.parse(["-"]).files == ["-"]),
    // "" is stdin (a file).
    harness.check("empty is stdin", options.parse([""]).files == [""]),
    // -- ends options.
    harness.check(
      "-- ends options",
      options.parse(["--", "-l"]).files == ["-l"],
    ),
    // -h: help.
    harness.check("-h help", options.parse(["-h"]).status == options.Help),
    harness.check(
      "--help help",
      options.parse(["--help"]).status == options.Help,
    ),
    // -V: version.
    harness.check("-V version", options.parse(["-V"]).status == options.Version),
    // Unknown flag: usage error.
    harness.check(
      "unknown flag usage error",
      case options.parse(["--bogus"]).status {
        options.UsageError(_) -> True
        _ -> False
      },
    ),
    // Flags after files still parse (wc allows it).
    harness.check(
      "flag after file",
      options.parse(["a.txt", "-l"]).figures
        == options.Figures(lines: True, words: False, bytes: False),
    ),
  ]
}
