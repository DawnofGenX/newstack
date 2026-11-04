package textstat

class CountsSuite extends munit.FunSuite:
  private def counts(text: String): Counts = Counts.ofBytes(text.getBytes("UTF-8"))

  test("plain text with a trailing newline") {
    assertEquals(counts("alpha beta\ngamma delta\n"), Counts(2L, 4L, 23L))
  }

  test("a last line without a trailing newline is not a line") {
    assertEquals(counts("alpha beta\ngamma"), Counts(1L, 3L, 16L))
  }

  test("bytes are bytes, not characters") {
    assertEquals(counts("h\u00e9llo w\u00f6rld\n"), Counts(1L, 2L, 14L))
  }

  test("empty input") {
    assertEquals(counts(""), Counts(0L, 0L, 0L))
  }

  test("runs of whitespace separate words, trailing space adds no word") {
    assertEquals(counts("  one\t\ttwo  \n\n three \n"), Counts(3L, 3L, 22L))
  }

  test("form feeds and vertical tabs are whitespace") {
    assertEquals(counts("a\u000bb\u000cc\n"), Counts(1L, 3L, 6L))
  }

  test("add sums every figure") {
    val total = Counts(1L, 2L, 3L).add(Counts(4L, 5L, 6L))
    assertEquals(total, Counts(5L, 7L, 9L))
  }
