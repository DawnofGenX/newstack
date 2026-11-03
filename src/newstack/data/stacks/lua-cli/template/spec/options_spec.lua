local harness = require("spec.harness")
local options = require("textstat.options")

local eq = harness.eq

harness.describe("options", function()
  harness.it("no arguments means every figure and stdin", function()
    local parsed = options.parse({})
    eq(parsed.status, "ok", "status")
    eq(parsed.mode, "all", "mode")
    eq(#parsed.files, 0, "files")
  end)

  harness.it("-l selects lines and keeps the file", function()
    local parsed = options.parse({ "-l", "a.txt" })
    eq(parsed.status, "ok", "status")
    eq(parsed.mode, "lines", "mode")
    eq(parsed.files, { "a.txt" }, "files")
  end)

  harness.it("--words is the long form of -w", function()
    eq(options.parse({ "--words" }).mode, "words", "mode")
  end)

  harness.it("repeating the same mode is allowed", function()
    eq(options.parse({ "-l", "--lines" }).mode, "lines", "mode")
    eq(options.parse({ "-c", "--bytes" }).mode, "bytes", "mode")
  end)

  harness.it("conflicting modes are a usage error", function()
    local parsed = options.parse({ "-l", "-c" })
    eq(parsed.status, "usage", "status")
    harness.contains(parsed.message, "conflicts", "message")
  end)

  harness.it("--help stops parsing", function()
    local parsed = options.parse({ "--help", "-l" })
    eq(parsed.status, "help", "status")
    eq(parsed.help, true, "help")
  end)

  harness.it("-h is the short form of --help", function()
    eq(options.parse({ "-h" }).status, "help", "status")
  end)

  harness.it("-V is a separate outcome from --help", function()
    eq(options.parse({ "-V" }).status, "version", "status")
  end)

  harness.it("an unknown flag is a usage error", function()
    local parsed = options.parse({ "--bogus" })
    eq(parsed.status, "usage", "status")
    harness.contains(parsed.message, "unknown option '--bogus'", "message")
  end)

  harness.it("-- ends option parsing", function()
    local parsed = options.parse({ "--", "-l" })
    eq(parsed.status, "ok", "status")
    eq(parsed.mode, "all", "mode")
    eq(parsed.files, { "-l" }, "files")
  end)

  harness.it("a bare - is standard input, not a flag", function()
    local parsed = options.parse({ "-" })
    eq(parsed.status, "ok", "status")
    eq(parsed.files, { "-" }, "files")
  end)

  harness.it("the usage line names the program it was given", function()
    harness.contains(options.usage("mytool"), "usage: mytool", "usage")
  end)
end)
