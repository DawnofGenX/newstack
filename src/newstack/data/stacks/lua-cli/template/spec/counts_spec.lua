local harness = require("spec.harness")
local counts = require("textstat.counts")

local eq = harness.eq

harness.describe("counts", function()
  harness.it("empty input has no lines, words or bytes", function()
    eq(counts.count(""), { lines = 0, words = 0, bytes = 0 })
  end)

  harness.it("a trailing newline counts as a line", function()
    eq(counts.count("hello\n"), { lines = 1, words = 1, bytes = 6 })
  end)

  harness.it("input without a trailing newline has no counted line", function()
    eq(counts.count("hello"), { lines = 0, words = 1, bytes = 5 })
  end)

  harness.it("runs of whitespace separate words without adding empty ones", function()
    eq(counts.count("  a   b  "), { lines = 0, words = 2, bytes = 9 })
  end)

  harness.it("tabs and carriage returns are whitespace, newline ends a line", function()
    eq(counts.count("\ta\r\nb\n"), { lines = 2, words = 2, bytes = 6 })
  end)

  harness.it("every line is counted once", function()
    eq(counts.count("one two\nthree\n"), { lines = 2, words = 3, bytes = 14 })
  end)

  harness.it("blank lines count as lines but not as words", function()
    eq(counts.count("a\n\n\nb\n"), { lines = 4, words = 2, bytes = 6 })
  end)

  harness.it("multi-byte characters count as their byte length", function()
    eq(counts.count("h\195\169llo\n"), { lines = 1, words = 1, bytes = 7 })
  end)

  harness.it("totals add field by field", function()
    eq(counts.add(counts.count("a b\n"), counts.count("c\n")),
      { lines = 2, words = 3, bytes = 6 })
  end)
end)
