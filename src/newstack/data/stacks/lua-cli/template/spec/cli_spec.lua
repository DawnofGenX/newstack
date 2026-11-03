-- Drives the real script as a subprocess: exit codes and stdout only count when
-- the shell produced them, not when a function returned them.

local harness = require("spec.harness")

local eq = harness.eq

local BINARY = "./bin/{{ npm_name }}"

local function shell_quote(path)
  return "'" .. tostring(path):gsub("'", "'\\''") .. "'"
end

local function run(command)
  local handle = assert(io.popen(command .. " 2>&1", "r"))
  local output = handle:read("*a") or ""
  local ok, _, code = handle:close()
  if ok then
    code = 0
  end
  return output, code
end

local function fields(output)
  local result = {}
  for token in output:gmatch("%S+") do
    result[#result + 1] = token
  end
  return result
end

local function with_file(contents, body)
  local path = os.tmpname()
  local handle = assert(io.open(path, "wb"))
  handle:write(contents)
  handle:close()
  local ok, err = pcall(body, path)
  os.remove(path)
  if not ok then
    error(err, 0)
  end
end

harness.describe("command line", function()
  harness.it("--help exits 0 and prints a usage line naming the binary", function()
    local output, code = run(BINARY .. " --help")
    eq(code, 0, "exit code")
    harness.contains(output, "usage: {{ npm_name }}", "stdout")
  end)

  harness.it("an unknown flag exits 2", function()
    local output, code = run(BINARY .. " --bogus")
    eq(code, 2, "exit code")
    harness.contains(output, "unknown option", "stderr")
  end)

  harness.it("a missing file exits 1", function()
    local output, code = run(BINARY .. " does-not-exist.txt")
    eq(code, 1, "exit code")
    harness.contains(output, "cannot open", "stderr")
  end)

  harness.it("a directory is a read error, not an empty file", function()
    local output, code = run(BINARY .. " .")
    eq(code, 1, "exit code")
    harness.contains(output, "cannot read", "stderr")
  end)

  harness.it("a file with a trailing newline is counted like wc", function()
    with_file("hello world\n", function(path)
      local output, code = run(BINARY .. " " .. shell_quote(path))
      eq(code, 0, "exit code")
      eq(fields(output), { "1", "2", "12", path }, "fields")
    end)
  end)

  harness.it("a file with no trailing newline reports zero lines", function()
    with_file("hello", function(path)
      local output, code = run(BINARY .. " " .. shell_quote(path))
      eq(code, 0, "exit code")
      eq(fields(output), { "0", "1", "5", path }, "fields")
    end)
  end)

  harness.it("-l prints only the line count", function()
    with_file("a\nb\n", function(path)
      local output, code = run(BINARY .. " -l " .. shell_quote(path))
      eq(code, 0, "exit code")
      eq(fields(output), { "2", path }, "fields")
    end)
  end)

  harness.it("standard input is counted when no file is given", function()
    local output, code = run("printf 'a b\\n' | " .. BINARY)
    eq(code, 0, "exit code")
    eq(fields(output), { "1", "2", "4" }, "fields")
  end)

  harness.it("several files print a total", function()
    with_file("a\n", function(first)
      with_file("b\n", function(second)
        local output, code = run(BINARY .. " " .. shell_quote(first) .. " " .. shell_quote(second))
        eq(code, 0, "exit code")
        local tokens = fields(output)
        eq(tokens[#tokens], "total", "total label")
        eq(tokens[#tokens - 3], "2", "total lines")
      end)
    end)
  end)
end)
