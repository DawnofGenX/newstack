local harness = require("spec.harness")
local describe, it, eq, contains = harness.describe, harness.it, harness.eq, harness.contains

local binary = "./bin/{{ npm_name }}"

local function run(arguments, input)
  local command = binary .. (arguments and (" " .. arguments) or "")
  if input then
    command = "printf " .. string.format("%q", input) .. " | " .. command
  end
  local handle = io.popen(command .. " 2>&1; echo \"[exit:$?]\"", "r")
  local output = handle:read("*a")
  handle:close()
  local status = tonumber(output:match("%[exit:(%d+)%]%s*$"))
  return (output:gsub("%[exit:%d+%]%s*$", "")), status
end

describe("cli", function()
  it("prints help", function()
    local output, status = run("--help")
    eq(status, 0)
    contains(output, "Usage:")
  end)

  it("validates valid input", function()
    local output, status = run("--check", '{"a":1}')
    eq(status, 0)
    eq(output:gsub("%s+$", ""), "valid")
  end)

  it("exits 1 on invalid input", function()
    local output, status = run("--check", '{"a":}')
    eq(status, 1)
    contains(output, "error:")
  end)

  it("reformats compact input", function()
    local output, status = run(nil, '{ "b": 2, "a": 1 }')
    eq(status, 0)
    contains(output, '"a":1')
    contains(output, '"b":2')
    eq(output:find(" ", 1, true), nil, "compact output has no spaces")
  end)

  it("canonicalises", function()
    local output, status = run("--canonical", '{"b":2,"a":1}')
    eq(status, 0)
    eq(output:gsub("%s+$", ""), '{"a":1,"b":2}')
  end)

  it("extracts a value with --get", function()
    local output, status = run("--get a.b[0]", '{"a":{"b":[5]}}')
    eq(status, 0)
    eq(output:gsub("%s+$", ""), "5")
  end)

  it("reports a missing path", function()
    local _, status = run("--get nope", '{"a":1}')
    eq(status, 1)
  end)

  it("rejects unknown flags with exit 2", function()
    local _, status = run("--bogus")
    eq(status, 2)
  end)

  it("reports a missing file", function()
    local _, status = run("no-such-file.json")
    eq(status, 1)
  end)
end)
