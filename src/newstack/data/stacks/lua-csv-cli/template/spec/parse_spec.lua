local harness = require("spec.harness")
local parse = require("csval.parse")

local eq = harness.eq

harness.describe("parse", function()
  harness.it("a single line without a newline is one row", function()
    eq(parse.parse("a,b"), { { "a", "b" } })
  end)

  harness.it("a trailing newline does not add an empty row", function()
    eq(parse.parse("a,b\n"), { { "a", "b" } })
  end)

  harness.it("blank lines between rows are kept as single empty fields", function()
    eq(parse.parse("a\n\nb\n"), { { "a" }, { "" }, { "b" } })
  end)

  harness.it("an empty trailing field survives", function()
    eq(parse.parse("a,\n"), { { "a", "" } })
  end)

  harness.it("doubled quotes inside a quoted field become one quote", function()
    eq(parse.parse('"he said ""hi""",b\n'), { { 'he said "hi"', "b" } })
  end)

  harness.it("a delimiter inside quotes is data", function()
    eq(parse.parse('"a,b",c\n'), { { "a,b", "c" } })
  end)

  harness.it("a newline inside quotes stays in the field", function()
    eq(parse.parse('"a\nb",c\n'), { { "a\nb", "c" } })
  end)

  harness.it("CRLF outside quotes ends a row and is not data", function()
    eq(parse.parse("a,b\r\nc,d\r\n"), { { "a", "b" }, { "c", "d" } })
  end)

  harness.it("a custom delimiter is honoured", function()
    eq(parse.parse("a\tb\n", "\t"), { { "a", "b" } })
  end)

  harness.it("quoted empty fields are empty strings", function()
    eq(parse.parse('"",x\n'), { { "", "x" } })
  end)

  harness.it("an unterminated quote is reported with its line", function()
    local ok, err = pcall(parse.parse, 'a,"b\n')
    eq(ok, false, "ok")
    harness.contains(err, "line 1: unterminated quoted field", "error")
  end)

  harness.it("a quote inside an unquoted field is rejected", function()
    local ok, err = pcall(parse.parse, 'a"b,c\n')
    eq(ok, false, "ok")
    harness.contains(err, "quote inside an unquoted field", "error")
  end)

  harness.it("rectangular rows pass the width check", function()
    parse.check_rectangular({ { "a", "b" }, { "c", "d" } })
    eq(true, true)
  end)

  harness.it("a ragged row is reported with its line number", function()
    local ok, err = pcall(parse.check_rectangular, { { "a", "b" }, { "c" } })
    eq(ok, false, "ok")
    harness.contains(err, "line 2: 1 field(s), expected 2", "error")
  end)
end)
