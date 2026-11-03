# Unit tests for the pure counting function. No I/O, no subprocess: these run
# in-process and pin the exact wc -l / -w / -c semantics.

describe("textstat_counts", function() {
  it("counts an empty input as zero", function() {
    expect_equal(textstat_counts(character(0)), list(lines = 0L, words = 0L, bytes = 0L), "empty character")
    expect_equal(textstat_counts(raw(0)), list(lines = 0L, words = 0L, bytes = 0L), "empty raw")
  })
  it("counts a single unterminated line as zero lines", function() {
    expect_equal(textstat_counts("hello"), list(lines = 0L, words = 1L, bytes = 5L), "no newline")
  })
  it("counts newline-terminated lines like wc -l", function() {
    expect_equal(textstat_counts("hello\n"), list(lines = 1L, words = 1L, bytes = 6L), "one line")
    expect_equal(textstat_counts("a\nb\nc\n"), list(lines = 3L, words = 3L, bytes = 6L), "three lines")
  })
  it("does not count a final line without a terminator", function() {
    expect_equal(textstat_counts("a\nb"), list(lines = 1L, words = 2L, bytes = 3L), "unterminated tail")
  })
  it("counts words as maximal non-whitespace runs", function() {
    expect_equal(textstat_counts("hello world\n"), list(lines = 1L, words = 2L, bytes = 12L), "two words")
    expect_equal(textstat_counts("  spaced   out  \n"), list(lines = 1L, words = 2L, bytes = 17L), "extra spaces")
  })
  it("treats tabs and carriage returns as word separators", function() {
    expect_equal(textstat_counts("a\tb\rc\n"), list(lines = 1L, words = 3L, bytes = 6L), "tab and cr")
  })
  it("counts multi-byte characters as their byte length", function() {
    expect_equal(textstat_counts(as.raw(c(0x68, 0xC3, 0xA9, 0x6C, 0x6C, 0x6F, 0x0A))),
                 list(lines = 1L, words = 1L, bytes = 7L), "utf-8 e-acute")
  })
})

describe("textstat_add", function() {
  it("adds two totals field by field", function() {
    a <- list(lines = 1L, words = 2L, bytes = 3L)
    b <- list(lines = 4L, words = 5L, bytes = 6L)
    expect_equal(textstat_add(a, b), list(lines = 5L, words = 7L, bytes = 9L), "sum")
  })
})
