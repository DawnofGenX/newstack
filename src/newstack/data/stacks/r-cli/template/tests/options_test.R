# Unit tests for the pure argument parser. Every branch is pinned here so the
# entry point never has to guess what a flag means.

describe("textstat_parse_args", function() {
  it("defaults to all fields with no files", function() {
    r <- textstat_parse_args(character(0))
    expect_equal(r$ok, TRUE, "ok")
    expect_equal(r$options$status, "ok", "status")
    expect_equal(r$options$mode, "all", "mode")
    expect_equal(r$options$files, character(0), "files")
  })
  it("recognises --help and -h", function() {
    expect_equal(textstat_parse_args("--help")$options$status, "help", "--help")
    expect_equal(textstat_parse_args("-h")$options$status, "help", "-h")
  })
  it("recognises --version and -V", function() {
    expect_equal(textstat_parse_args("--version")$options$status, "version", "--version")
    expect_equal(textstat_parse_args("-V")$options$status, "version", "-V")
  })
  it("maps short and long mode flags", function() {
    expect_equal(textstat_parse_args("-l")$options$mode, "lines", "-l")
    expect_equal(textstat_parse_args("--lines")$options$mode, "lines", "--lines")
    expect_equal(textstat_parse_args("-w")$options$mode, "words", "-w")
    expect_equal(textstat_parse_args("--words")$options$mode, "words", "--words")
    expect_equal(textstat_parse_args("-c")$options$mode, "bytes", "-c")
    expect_equal(textstat_parse_args("--bytes")$options$mode, "bytes", "--bytes")
  })
  it("collects multiple files", function() {
    r <- textstat_parse_args(c("a.txt", "b.txt"))
    expect_equal(r$options$files, c("a.txt", "b.txt"), "two files")
  })
  it("treats a bare dash and empty string as files", function() {
    r <- textstat_parse_args(c("-", ""))
    expect_equal(r$options$files, c("-", ""), "dash and empty")
  })
  it("stops parsing options after --", function() {
    r <- textstat_parse_args(c("--", "-l"))
    expect_equal(r$options$files, "-l", "-l is a file after --")
    expect_equal(r$options$mode, "all", "mode stays all")
  })
  it("rejects an unknown option", function() {
    r <- textstat_parse_args("--bogus")
    expect_equal(r$ok, FALSE, "not ok")
    expect_equal(r$reason, "unknown option '--bogus'", "reason")
  })
  it("rejects conflicting modes", function() {
    r <- textstat_parse_args(c("-l", "-w"))
    expect_equal(r$ok, FALSE, "not ok")
    expect_equal(grepl("conflicts", r$reason), TRUE, "reason mentions conflict")
  })
})
