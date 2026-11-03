# Pure counting: no I/O, no prints, no quit(). The entry point reads the bytes;
# every decision about what a line, a word and a byte are lives here, so the
# tests can drive this function directly.

# Counts newlines, whitespace-separated words and raw bytes.
#
# Lines follow `wc -l`: the number of "\n" bytes, so a final line without a
# terminator is not counted. Words are maximal runs of non-whitespace bytes and
# `bytes` is the length of the raw input, which is what `wc -c` reports. This is
# the same contract as the other newstack CLI stacks.
#
# @param data a raw vector (preferred, byte-accurate) or a character string
# @return a named list: list(lines = integer, words = integer, bytes = integer)
textstat_counts <- function(data) {
  if (is.character(data)) {
    # charToRaw needs a length-1 character vector; anything else is treated as
    # empty so the function stays total.
    data <- if (length(data) == 1L) charToRaw(data) else raw(0)
  }
  if (!is.raw(data) || length(data) == 0L) {
    return(list(lines = 0L, words = 0L, bytes = 0L))
  }
  n <- length(data)
  lines <- as.integer(sum(data == as.raw(10L)))
  # wc -w treats every isspace() byte as a separator, newline included.
  ws <- c(as.raw(32L), as.raw(9L), as.raw(10L), as.raw(13L), as.raw(11L), as.raw(12L))
  is_ws <- data %in% ws
  # A word starts at a non-whitespace byte whose predecessor is whitespace (or
  # the start of the input). Vectorised, so it stays fast on large files.
  starts <- !is_ws & c(TRUE, is_ws[-n])
  words <- as.integer(sum(starts))
  list(lines = lines, words = words, bytes = as.integer(n))
}

# Adds two totals field by field, so several files can be reported as one.
#
# @param left  a counts list from textstat_counts()
# @param right a counts list from textstat_counts()
# @return a counts list
textstat_add <- function(left, right) {
  list(
    lines = left$lines + right$lines,
    words = left$words + right$words,
    bytes = left$bytes + right$bytes
  )
}
