# A tiny base-R assertion harness: no testthat, no renv, no network.
#
# expect_equal(actual, expected, message) records a pass or a failure and
# keeps going, so one bad case does not hide the rest. run.R sources this file
# and then every *_test.R, and finally prints a summary and exits non-zero if
# anything failed.

textstat_pass <- 0L
textstat_fail <- 0L
textstat_failures <- character(0)

expect_equal <- function(actual, expected, message = "") {
  ok <- identical(actual, expected)
  if (ok) {
    textstat_pass <<- textstat_pass + 1L
    cat(sprintf("  ok   %s\n", message))
  } else {
    textstat_fail <<- textstat_fail + 1L
    textstat_failures <<- c(textstat_failures, message)
    cat(sprintf("  FAIL %s\n", message))
    cat(sprintf("       expected: %s\n", paste(deparse(expected), collapse = " ")))
    cat(sprintf("       actual:   %s\n", paste(deparse(actual), collapse = " ")))
  }
  invisible(ok)
}

# Group tests under a heading so the output is scannable.
describe <- function(name, fn) {
  cat(sprintf("\n%s\n", name))
  fn()
}

# Run a single named test. The name is for readability; the assertions inside
# do the real work.
it <- function(name, fn) {
  fn()
}

# Print the summary and exit non-zero if any expectation failed.
finish <- function() {
  cat(sprintf("\n%d passed, %d failed\n", textstat_pass, textstat_fail))
  if (textstat_fail > 0L) {
    cat("failures:\n")
    for (f in textstat_failures) cat("  - ", f, "\n", sep = "")
    quit(status = 1L)
  }
  quit(status = 0L)
}
