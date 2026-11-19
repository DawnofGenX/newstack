(* wc semantics: trailing newline, whitespace, UTF-8 bytes. *)

let () =
  let c = Counts.of_bytes "" in
  Harness.check_eq "empty: lines" 0 c.lines;
  Harness.check_eq "empty: words" 0 c.words;
  Harness.check_eq "empty: bytes" 0 c.bytes;

  let c = Counts.of_bytes "hello\n" in
  Harness.check_eq "newline: lines" 1 c.lines;
  Harness.check_eq "newline: words" 1 c.words;
  Harness.check_eq "newline: bytes" 6 c.bytes;

  let c = Counts.of_bytes "hello" in
  Harness.check_eq "no trailing newline: lines" 0 c.lines;
  Harness.check_eq "no trailing newline: words" 1 c.words;
  Harness.check_eq "no trailing newline: bytes" 5 c.bytes;

  let c = Counts.of_bytes "a b\n" in
  Harness.check_eq "two words: lines" 1 c.lines;
  Harness.check_eq "two words: words" 2 c.words;
  Harness.check_eq "two words: bytes" 4 c.bytes;

  let c = Counts.of_bytes "  a  b  \n" in
  Harness.check_eq "padded: words" 2 c.words;
  Harness.check_eq "padded: bytes" 9 c.bytes;

  let c = Counts.of_bytes "a\n\nb\n" in
  Harness.check_eq "blank line: lines" 3 c.lines;
  Harness.check_eq "blank line: words" 2 c.words;

  let c = Counts.of_bytes "a\tb\n" in
  Harness.check_eq "tab: words" 2 c.words;

  let c = Counts.of_bytes "a\r\nb\r\n" in
  Harness.check_eq "crlf: lines" 2 c.lines;
  Harness.check_eq "crlf: words" 2 c.words;

  let c = Counts.of_bytes "héllo wörld\n" in
  Harness.check_eq "utf8: words" 2 c.words;
  Harness.check_eq "utf8: bytes" 14 c.bytes;

  let a = Counts.of_bytes "a b\n" in
  let b = Counts.of_bytes "c\n" in
  let s = Counts.add a b in
  Harness.check_eq "add: lines" 2 s.lines;
  Harness.check_eq "add: words" 3 s.words;
  Harness.check_eq "add: bytes" 6 s.bytes;

  Harness.finish ()
