# End-to-end tests: spawn the real entry point and assert on its output and
# exit code. The binary is invoked through Rscript so the tests do not depend
# on the executable bit.

binary <- file.path(root, "bin", "{{ npm_name }}")

run_cli <- function(...) {
  args <- as.character(list(...))
  cmd <- paste(c("Rscript", shQuote(binary), args), collapse = " ")
  out <- system(paste0(cmd, " 2>&1"), intern = TRUE)
  status <- attr(out, "status")
  if (is.null(status)) status <- 0L
  list(output = paste(out, collapse = "\n"), status = as.integer(status))
}

# Split a line of wc-style output into its whitespace-separated tokens.
fields <- function(line) {
  toks <- strsplit(line, "\\s+")[[1]]
  toks[toks != ""]
}

# Write a temp file, run fn on its path, and clean up afterwards.
with_file <- function(contents, fn) {
  path <- tempfile(fileext = ".txt")
  writeBin(charToRaw(contents), path)
  on.exit(unlink(path))
  fn(path)
}

describe("cli", function() {
  it("--help exits 0 and prints usage", function() {
    r <- run_cli("--help")
    expect_equal(r$status, 0L, "exit code")
    expect_equal(grepl("usage:", r$output), TRUE, "prints usage")
  })
  it("an unknown flag exits 2", function() {
    r <- run_cli("--bogus")
    expect_equal(r$status, 2L, "exit code")
    expect_equal(grepl("unknown option", r$output), TRUE, "prints reason")
  })
  it("a missing file exits 1", function() {
    r <- run_cli("does-not-exist.txt")
    expect_equal(r$status, 1L, "exit code")
    expect_equal(grepl("No such file", r$output), TRUE, "prints reason")
  })
  it("counts a file like wc", function() {
    with_file("hello world\n", function(path) {
      r <- run_cli(path)
      expect_equal(r$status, 0L, "exit code")
      expect_equal(fields(r$output), c("1", "2", "12", path), "fields")
    })
  })
  it("prints a total row for multiple files", function() {
    p1 <- tempfile(fileext = ".txt"); writeBin(charToRaw("a\n"), p1)
    p2 <- tempfile(fileext = ".txt"); writeBin(charToRaw("b\n"), p2)
    on.exit(unlink(c(p1, p2)))
    r <- run_cli(p1, p2)
    expect_equal(r$status, 0L, "exit code")
    lines <- strsplit(r$output, "\n")[[1]]
    expect_equal(length(lines), 3L, "three rows")
    expect_equal(fields(lines[3]), c("2", "2", "4", "total"), "total row")
  })
  it("standard input is counted when no file is given", function() {
    cmd <- paste0("printf 'a b\\n' | Rscript ", shQuote(binary), " 2>&1")
    out <- system(cmd, intern = TRUE)
    status <- attr(out, "status")
    if (is.null(status)) status <- 0L
    expect_equal(as.integer(status), 0L, "exit code")
    expect_equal(fields(paste(out, collapse = "\n")), c("1", "2", "4"), "fields")
  })
})
