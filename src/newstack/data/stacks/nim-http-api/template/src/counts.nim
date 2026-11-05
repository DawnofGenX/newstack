## Counting rules shared by the CLI and the service.
##
## A line is a ``\n`` byte, a word is a maximal run of non-space bytes, and
## ``bytes`` is the raw UTF-8 length of the string (Nim strings are byte
## buffers, so ``len`` is already the byte count).

import std/json
import std/strutils

type
  Counts* = object
    lines*: int
    words*: int
    bytes*: int

proc countText*(text: string): Counts =
  ## Counts lines, words and bytes in `text`.
  var words = 0
  var inWord = false
  for ch in text:
    let space = ch in {' ', '\t', '\n', '\r', '\v', '\f'}
    if space:
      inWord = false
    elif not inWord:
      inWord = true
      inc words
  Counts(
    lines: text.count('\n'),
    words: words,
    bytes: text.len,
  )

proc countsJson*(text: string, counts: Counts): JsonNode =
  ## The JSON body every counting endpoint returns.
  %*{
    "text": text,
    "lines": counts.lines,
    "words": counts.words,
    "bytes": counts.bytes,
  }
