describe("textstat_counts", function() {
  it("counts lines, words and bytes the way wc does", function() {
    expect_equal(
      textstat_counts("hello world\n"),
      list(lines = 1L, words = 2L, bytes = 12L),
      "one line, two words, twelve bytes"
    )
    expect_equal(
      textstat_counts("a b\nc\n"),
      list(lines = 2L, words = 3L, bytes = 6L),
      "a final newline does not open a third line"
    )
    expect_equal(
      textstat_counts(""),
      list(lines = 0L, words = 0L, bytes = 0L),
      "the empty string is all zeros"
    )
    expect_equal(
      textstat_counts("\n\nx\n"),
      list(lines = 3L, words = 1L, bytes = 4L),
      "blank lines are lines"
    )
    expect_equal(
      textstat_counts("abc"),
      list(lines = 0L, words = 1L, bytes = 3L),
      "a line without a newline is not a line"
    )
  })

  it("counts whitespace runs as one separator", function() {
    expect_equal(
      textstat_counts("  \t "),
      list(lines = 0L, words = 0L, bytes = 4L),
      "only whitespace: no words, four bytes"
    )
    expect_equal(
      textstat_counts("  padded  \n"),
      list(lines = 1L, words = 1L, bytes = 11L),
      "the text is counted exactly as sent, padding included"
    )
  })

  it("counts bytes as UTF-8, not as characters", function() {
    expect_equal(
      textstat_counts("h\u00e9llo w\u00f6rld\n"),
      list(lines = 1L, words = 2L, bytes = 14L),
      "two accented characters add two bytes"
    )
    expect_equal(
      textstat_counts("\U0001F642\n"),
      list(lines = 1L, words = 1L, bytes = 5L),
      "a single emoji is four bytes"
    )
  })

  it("refuses anything that is not one string", function() {
    failed <- tryCatch({
      textstat_counts(42)
      FALSE
    }, error = function(e) grepl("expects a single string", conditionMessage(e)))
    expect_equal(failed, TRUE, "a number is rejected with a clear message")
  })
})

describe("textstat_payload", function() {
  it("echoes the text next to its counts", function() {
    expect_equal(
      textstat_payload("a b\nc\n"),
      list(text = "a b\nc\n", lines = 2L, words = 3L, bytes = 6L),
      "the response body carries text, lines, words and bytes"
    )
  })
})
