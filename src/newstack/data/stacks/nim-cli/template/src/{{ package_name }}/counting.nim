## Line, word and byte counting — the only place that decides an answer.
##
## Pure functions only: no files, no stdout, no globals. The entry point reads
## bytes and prints them; this module just counts, which is what the tests drive
## directly.

type
  Counts* = object
    ## Totals for one input.
    lines*: int ## `'\n'` characters, which is what `wc -l` reports.
    words*: int ## Runs of non-whitespace characters, like `wc -w`.
    bytes*: int ## Raw bytes, which is what `wc -c` reports for UTF-8 text.

func count*(text: string): Counts =
  ## Counts `text`. `'\n'` is the only line separator, as in `wc`.
  ##
  ## Rob Pike's state machine: walk the bytes once, remember whether the
  ## previous byte was inside a word. Empty input stays all-zero.
  var inWord = false
  for ch in text:
    case ch
    of '\n':
      inc result.lines
      inWord = false
    of ' ', '\t', '\r', '\v', '\f':
      inWord = false
    else:
      if not inWord:
        inc result.words
        inWord = true
  result.bytes = text.len

func `+`*(a, b: Counts): Counts =
  ## Adds two totals, so several files can be reported as one.
  Counts(
    lines: a.lines + b.lines,
    words: a.words + b.words,
    bytes: a.bytes + b.bytes,
  )

func `$`*(counts: Counts): string =
  ## Debug form; the CLI does its own right-aligned formatting.
  "Counts(lines: " & $counts.lines & ", words: " & $counts.words &
    ", bytes: " & $counts.bytes & ")"
