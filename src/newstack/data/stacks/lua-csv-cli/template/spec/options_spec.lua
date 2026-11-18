local harness = require("spec.harness")
local options = require("csval.options")

local eq = harness.eq
local parse = options.parse

harness.describe("options", function()
  harness.it("defaults are csv output with a header and no file", function()
    local parsed = parse({})
    eq(parsed.status, "ok")
    eq(parsed.output, "csv")
    eq(parsed.header, true)
    eq(parsed.delimiter, ",")
    eq(#parsed.files, 0)
  end)

  harness.it("--help sets the help status", function()
    eq(parse({ "--help" }).status, "help")
    eq(parse({ "-h" }).status, "help")
  end)

  harness.it("--version sets the version status", function()
    eq(parse({ "-V" }).status, "version")
  end)

  harness.it("--columns takes the next argument", function()
    eq(parse({ "-c", "id,name" }).columns, "id,name")
    eq(parse({ "--columns=id" }).columns, "id")
  end)

  harness.it("a missing option value is a usage error", function()
    local parsed = parse({ "--columns" })
    eq(parsed.status, "usage")
    harness.contains(parsed.message, "needs a value", "message")
  end)

  harness.it("--delimiter accepts tab by name", function()
    eq(parse({ "-d", "tab" }).delimiter, "\t")
    eq(parse({ "-d", ";" }).delimiter, ";")
  end)

  harness.it("a multi-byte delimiter is a usage error", function()
    eq(parse({ "-d", "ab" }).status, "usage")
  end)

  harness.it("only csv, tsv and json are accepted outputs", function()
    eq(parse({ "-o", "tsv" }).output, "tsv")
    eq(parse({ "-o", "yaml" }).status, "usage")
  end)

  harness.it("--no-header turns the header off", function()
    eq(parse({ "--no-header" }).header, false)
  end)

  harness.it("an unknown flag is a usage error", function()
    local parsed = parse({ "--bogus" })
    eq(parsed.status, "usage")
    harness.contains(parsed.message, "unknown option '--bogus'", "message")
  end)

  harness.it("a bare dash is a file, and -- ends option parsing", function()
    eq(parse({ "--", "--not-a-flag" }).files[1], "--not-a-flag")
    eq(parse({ "-" }).files[1], "-")
  end)

  harness.it("the usage line names the program it was given", function()
    harness.contains(options.usage("csval-cli"), "usage: csval-cli", "usage")
  end)
end)
