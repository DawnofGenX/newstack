let () =
  let open Harness in
  let counts text = Counts.of_bytes text in
  check "empty" (counts "" = { Counts.lines = 0; words = 0; bytes = 0 });
  check "one line" (counts "hello world\n" = { Counts.lines = 1; words = 2; bytes = 12 });
  check "two lines" (counts "one two\nthree\n" = { Counts.lines = 2; words = 3; bytes = 14 });
  check "blank lines" (counts "\n\nx\n" = { Counts.lines = 3; words = 1; bytes = 4 });
  check "only spaces" (counts "  \t " = { Counts.lines = 0; words = 0; bytes = 4 });
  check "no newline" (counts "abc" = { Counts.lines = 0; words = 1; bytes = 3 });
  check "utf8 bytes" (counts "héllo wörld\n" = { Counts.lines = 1; words = 2; bytes = 14 });
  check "emoji" (counts "🙂\n" = { Counts.lines = 1; words = 1; bytes = 5 });
  finish ()
