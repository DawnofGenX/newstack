import harness
import textstat/counts

/// Run the counts tests. Returns a list of failed check names (empty if all
/// pass).
pub fn run() -> List(String) {
  let empty = counts.of_bytes(<<>>)
  let trailing = counts.of_bytes(<<"alpha beta\ngamma delta\n">>)
  let no_trailing = counts.of_bytes(<<"no trailing newline">>)
  let utf8 = counts.of_bytes(<<"héllo wörld\n">>)
  let control =
    counts.of_bytes(<<
      "a\u{0009}b\u{000D}c\u{000A}d\u{000B}e\u{000C}f\u{000D}g\u{000A}",
    >>)
  [
    // Empty input.
    harness.check_eq("empty lines", empty.lines, 0),
    harness.check_eq("empty words", empty.words, 0),
    harness.check_eq("empty bytes", empty.bytes, 0),
    // Trailing newline: 2 lines, 4 words, 23 bytes.
    harness.check_eq("trailing lines", trailing.lines, 2),
    harness.check_eq("trailing words", trailing.words, 4),
    harness.check_eq("trailing bytes", trailing.bytes, 23),
    // No trailing newline: 0 lines (wc -l), 3 words, 19 bytes.
    harness.check_eq("no-trailing lines", no_trailing.lines, 0),
    harness.check_eq("no-trailing words", no_trailing.words, 3),
    harness.check_eq("no-trailing bytes", no_trailing.bytes, 19),
    // UTF-8: héllo wörld\n = 1 line, 2 words, 14 bytes (byte-accurate).
    harness.check_eq("utf8 lines", utf8.lines, 1),
    harness.check_eq("utf8 words", utf8.words, 2),
    harness.check_eq("utf8 bytes", utf8.bytes, 14),
    // Control chars: a\tb\rc\nd\ve\ff\rg\n = 2 lines, 7 words, 14 bytes.
    harness.check_eq("control lines", control.lines, 2),
    harness.check_eq("control words", control.words, 7),
    harness.check_eq("control bytes", control.bytes, 14),
    // add: totals.
    harness.check_eq("add lines", counts.add(empty, trailing).lines, 2),
    harness.check_eq("add bytes", counts.add(empty, trailing).bytes, 23),
  ]
}
