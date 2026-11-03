# Command line parsing: argv in, an options list out. No printing, no quit(),
# so every branch is a unit test rather than a subprocess.

textstat_version <- "0.1.0"

# The help text. The caller passes the program name so the usage line names
# the binary that is actually being run.
#
# @param program string
# @return string
textstat_usage <- function(program) {
  paste0(
    "usage: ", program, " [-l | -w | -c] [--] [FILE ...]\n",
    "\n",
    "Count lines, words and bytes in each FILE, or in standard input\n",
    "when no FILE is given. With more than one FILE a total is printed.\n",
    "\n",
    "  -l, --lines     print the line count only\n",
    "  -w, --words     print the word count only\n",
    "  -c, --bytes     print the byte count only\n",
    "  -h, --help      show this help and exit\n",
    "  -V, --version   show the version and exit\n"
  )
}

# Parses an argv vector (without the program name).
#
# Hand-rolled on purpose: an explicit loop keeps `--`, a bare `-` and
# conflicting modes obvious, and every branch below is pinned by a test.
#
# @param argv character vector of arguments
# @return list(ok = TRUE, options = list(status, mode, files)) on success, or
#         list(ok = FALSE, reason = string) on a usage error
textstat_parse_args <- function(argv) {
  modes <- c(
    "-l" = "lines", "--lines" = "lines",
    "-w" = "words", "--words" = "words",
    "-c" = "bytes", "--bytes" = "bytes"
  )

  mode <- "all"
  chosen <- FALSE
  options_ended <- FALSE
  files <- character(0)

  for (value in as.character(argv)) {
    if (options_ended || value == "" || value == "-") {
      files <- c(files, value)
    } else if (value == "--") {
      options_ended <- TRUE
    } else if (value == "-h" || value == "--help") {
      return(list(ok = TRUE, options = list(status = "help", mode = mode, files = files)))
    } else if (value == "-V" || value == "--version") {
      return(list(ok = TRUE, options = list(status = "version", mode = mode, files = files)))
    } else if (value %in% names(modes)) {
      m <- modes[[value]]
      if (chosen && mode != m) {
        return(list(ok = FALSE, reason = paste0(
          "choose one of -l, -w, -c: '", value, "' conflicts with an earlier mode"
        )))
      }
      chosen <- TRUE
      mode <- m
    } else if (startsWith(value, "-")) {
      return(list(ok = FALSE, reason = paste0("unknown option '", value, "'")))
    } else {
      files <- c(files, value)
    }
  }

  list(ok = TRUE, options = list(status = "ok", mode = mode, files = files))
}
