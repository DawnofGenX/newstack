--! Rendering: rows back to CSV, TSV or JSON. Pure functions, no I/O.

local M = {}

--- True when a field has to be quoted to survive a round trip.
local function needs_quotes(field, delimiter)
  return field:find(delimiter, 1, true) ~= nil
    or field:find('"', 1, true) ~= nil
    or field:find("[\r\n]") ~= nil
    or field:sub(1, 1) == " "
    or field:sub(-1) == " "
end

--- Renders rows as delimited text, quoting only the fields that need it.
---
--- @param rows table
--- @param delimiter string|nil default ","
--- @return string
function M.render(rows, delimiter)
  delimiter = delimiter or ","
  local lines = {}
  for _, row in ipairs(rows) do
    local fields = {}
    for position, field in ipairs(row) do
      field = tostring(field)
      if needs_quotes(field, delimiter) then
        fields[position] = '"' .. field:gsub('"', '""') .. '"'
      else
        fields[position] = field
      end
    end
    lines[#lines + 1] = table.concat(fields, delimiter)
  end
  if #lines == 0 then
    return ""
  end
  return table.concat(lines, "\n") .. "\n"
end

local ESCAPES = {
  ['"'] = '\\"',
  ["\\"] = "\\\\",
  ["\n"] = "\\n",
  ["\r"] = "\\r",
  ["\t"] = "\\t",
  ["\b"] = "\\b",
  ["\f"] = "\\f",
}

local function quote(text)
  return '"' .. text:gsub('[%c"\\]', function(char)
    return ESCAPES[char] or string.format("\\u%04x", char:byte())
  end) .. '"'
end

--- Encodes a value as JSON. Lists stay lists; an empty table encodes as [].
---
--- @param value any
--- @return string
function M.encode(value)
  local kind = type(value)
  if kind == "string" then
    return quote(value)
  elseif kind == "number" then
    if math.type(value) == "integer" then
      return string.format("%d", value)
    end
    return string.format("%.17g", value)
  elseif kind == "boolean" then
    return tostring(value)
  elseif kind == "table" then
    local parts = {}
    if #value > 0 or next(value) == nil then
      for _, item in ipairs(value) do
        parts[#parts + 1] = M.encode(item)
      end
      return "[" .. table.concat(parts, ",") .. "]"
    end
    local keys = {}
    for key in pairs(value) do
      keys[#keys + 1] = tostring(key)
    end
    table.sort(keys)
    for _, key in ipairs(keys) do
      parts[#parts + 1] = quote(key) .. ":" .. M.encode(value[key])
    end
    return "{" .. table.concat(parts, ",") .. "}"
  end
  return "null"
end

return M
