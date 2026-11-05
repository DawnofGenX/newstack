# Pure counting: no I/O, no prints, no quit(), so the tests can drive it.
#
# Lines follow `wc -l` (the number of "\n" bytes), words are maximal runs of
# non-whitespace bytes, and bytes is the UTF-8 length of the text - the same
# contract as every other newstack service stack.

# Counts lines, words and bytes of one string.
#
# @param text a length-1 character vector
# @return a named list: list(lines = integer, words = integer, bytes = integer)
textstat_counts <- function(text) {
  if (!is.character(text) || length(text) != 1L) {
    stop("textstat_counts() expects a single string", call. = FALSE)
  }
  data <- if (nchar(text, type = "bytes") == 0L) raw(0) else charToRaw(enc2utf8(text))
  n <- length(data)
  if (n == 0L) {
    return(list(lines = 0L, words = 0L, bytes = 0L))
  }
  lines <- as.integer(sum(data == as.raw(10L)))
  ws <- c(as.raw(32L), as.raw(9L), as.raw(10L), as.raw(13L), as.raw(11L), as.raw(12L))
  is_ws <- data %in% ws
  starts <- !is_ws & c(TRUE, is_ws[-n])
  list(lines = lines, words = as.integer(sum(starts)), bytes = as.integer(n))
}

# The response body for a counted string: the text echoed back with its counts,
# which is what GET/POST /stats answer.
#
# @param text the counted string
# @return a named list ready for the JSON serializer
textstat_payload <- function(text) {
  counts <- textstat_counts(text)
  list(text = text, lines = counts$lines, words = counts$words, bytes = counts$bytes)
}
