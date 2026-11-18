-- Drives the real script as a subprocess: exit codes and stdout only count when
-- the shell produced them, not when a function returned them.

local harness = require("spec.harness")

local eq = harness.eq
local BINARY = "./bin/{{ npm_name }}"

local function run(command)
  local handle = assert(io.popen(command .. " 2>&1", "r"))
  local output = handle:read("*a") or ""
  local ok, _, code = handle:close()
  if ok then
    code = 0
  end
  return output, code
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
  harness.it("--help exits 0 and names the binary", function()
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
    local output, code = run(BINARY .. " does-not-exist.csv")
    eq(code, 1, "exit code")
    harness.contains(output, "cannot open", "stderr")
  end)

  harness.it("standard input is read when no file is given", function()
    local output, code = run("printf 'id,name\\n1,alpha\\n' | " .. BINARY)
    eq(code, 0, "exit code")
    eq(output, "id,name\n1,alpha\n")
  end)

  harness.it("--columns projects and reorders", function()
    with_file("id,name,amount\n1,alpha,10\n", function(path)
      local output, code = run(BINARY .. " -c amount,id " .. path)
      eq(code, 0, "exit code")
      eq(output, "amount,id\n10,1\n")
    end)
  end)

  harness.it("a quoted field with a comma round-trips", function()
    with_file('id,note\n1,"a,b"\n', function(path)
      local output, code = run(BINARY .. " " .. path)
      eq(code, 0, "exit code")
      eq(output, 'id,note\n1,"a,b"\n')
    end)
  end)

  harness.it("tsv output replaces the delimiter", function()
    with_file("a,b\n1,2\n", function(path)
      local output, code = run(BINARY .. " -o tsv " .. path)
      eq(code, 0, "exit code")
      eq(output, "a\tb\n1\t2\n")
    end)
  end)

  harness.it("json output is an array of objects when there is a header", function()
    with_file("id,name\n1,alpha\n", function(path)
      local output, code = run(BINARY .. " -o json " .. path)
      eq(code, 0, "exit code")
      eq(output, '[{"id":"1","name":"alpha"}]\n')
    end)
  end)

  harness.it("json output is an array of arrays with --no-header", function()
    with_file("1,alpha\n", function(path)
      local output, code = run(BINARY .. " -o json --no-header " .. path)
      eq(code, 0, "exit code")
      eq(output, '[["1","alpha"]]\n')
    end)
  end)

  harness.it("a semicolon file is parsed with -d", function()
    with_file("a;b\n1;2\n", function(path)
      local output, code = run(BINARY .. " -d ';' " .. path)
      eq(code, 0, "exit code")
      eq(output, "a,b\n1,2\n")
    end)
  end)

  harness.it("a ragged file exits 1 and names the line", function()
    with_file("a,b\n1\n", function(path)
      local output, code = run(BINARY .. " " .. path)
      eq(code, 1, "exit code")
      harness.contains(output, "line 2:", "stderr")
    end)
  end)

  harness.it("an unknown column exits 2", function()
    with_file("a,b\n1,2\n", function(path)
      local output, code = run(BINARY .. " -c nope " .. path)
      eq(code, 2, "exit code")
      harness.contains(output, "unknown column 'nope'", "stderr")
    end)
  end)
end)
