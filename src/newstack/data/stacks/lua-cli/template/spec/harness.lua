-- Minimal test harness: describe/it/eq, Lua 5.4 standard library only.
--
-- The runner stops at the first failure and exits non-zero, so a broken build is
-- obvious in CI without a dependency on busted or luarocks.

local M = {}

local passed, failed = 0, 0
local current = "?"

local function sorted_keys(value)
  local keys = {}
  for key in pairs(value) do
    keys[#keys + 1] = tostring(key)
  end
  table.sort(keys)
  return keys
end

local function show(value)
  if type(value) == "table" then
    local parts = {}
    for _, key in ipairs(sorted_keys(value)) do
      parts[#parts + 1] = key .. "=" .. show(value[key])
    end
    return "{" .. table.concat(parts, ", ") .. "}"
  elseif type(value) == "string" then
    return string.format("%q", value)
  end
  return tostring(value)
end

local function deep_equal(left, right)
  if left == right then
    return true
  end
  if type(left) ~= "table" or type(right) ~= "table" then
    return false
  end
  for key, value in pairs(left) do
    if not deep_equal(value, right[key]) then
      return false
    end
  end
  for key in pairs(right) do
    if left[key] == nil then
      return false
    end
  end
  return true
end

--- Groups the tests that follow under a name.
function M.describe(name, body)
  current = name
  body()
end

--- Runs one test. The first failure prints the mismatch and exits 1.
function M.it(name, body)
  local ok, err = pcall(body)
  if ok then
    passed = passed + 1
    io.stdout:write(string.format("ok %d - %s: %s\n", passed + failed, current, name))
    return
  end
  failed = failed + 1
  io.stdout:write(string.format("not ok - %s: %s\n", current, name))
  io.stdout:write("  " .. tostring(err) .. "\n")
  io.stdout:write(string.format("%d passed, %d failed\n", passed, failed))
  os.exit(1)
end

--- Asserts equality, reporting both sides with an optional label.
function M.eq(got, want, label)
  if not deep_equal(got, want) then
    error(string.format(
      "%s: expected %s, got %s",
      label or "value",
      show(want),
      show(got)
    ), 2)
  end
end

--- Asserts that text contains a substring.
function M.contains(haystack, needle, label)
  if type(haystack) ~= "string" or not haystack:find(needle, 1, true) then
    error(string.format(
      "%s: expected %q to contain %q",
      label or "text",
      tostring(haystack),
      tostring(needle)
    ), 2)
  end
end

--- Prints the summary and exits 0 only when every test passed.
function M.finish()
  io.stdout:write(string.format("%d passed, %d failed\n", passed, failed))
  os.exit(failed == 0 and 0 or 1)
end

return M
