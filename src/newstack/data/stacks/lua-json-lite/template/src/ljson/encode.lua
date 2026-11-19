-- JSON serialisation with three shapes the CLI exposes: compact, two-space
-- pretty, and "canonical" (object keys sorted, so two documents that mean the
-- same thing serialise to the same bytes).

local decode = require("ljson.decode")

local M = {}

local escape_map = {
  ['"'] = '\\"', ["\\"] = "\\\\", ["\b"] = "\\b",
  ["\f"] = "\\f", ["\n"] = "\\n", ["\r"] = "\\r", ["\t"] = "\\t",
}

local function escape_string(text)
  return (text:gsub('[%c"\\]', function(character)
    return escape_map[character] or string.format("\\u%04x", character:byte())
  end))
end

local function number_to_string(value)
  if value ~= value or value == math.huge or value == -math.huge then
    error("cannot serialise a non-finite number", 0)
  end
  if value == math.floor(value) and math.abs(value) < 1e15 then
    return string.format("%d", value)
  end
  return string.format("%.14g", value)
end

local function ordered_keys(value, canonical)
  local keys = {}
  for key in pairs(value) do
    if type(key) ~= "string" and type(key) ~= "number" then
      error("object keys must be strings or numbers, got " .. type(key), 0)
    end
    keys[#keys + 1] = key
  end
  if canonical then
    table.sort(keys, function(left, right)
      local left_is_number, right_is_number = type(left) == "number", type(right) == "number"
      if left_is_number and right_is_number then
        return left < right
      elseif left_is_number ~= right_is_number then
        return left_is_number
      end
      return left < right
    end)
  end
  return keys
end

local function is_array(value)
  local metatable = getmetatable(value)
  if metatable and metatable.__json_object then
    return false
  end
  local count = 0
  for key in pairs(value) do
    if type(key) ~= "number" or key ~= math.floor(key) or key < 1 then
      return false
    end
    count = count + 1
  end
  return count == #value
end

local write_value

local function write_table(value, options, depth)
  if value == decode.null then
    return "null"
  end
  local indent = options.pretty and ("\n" .. string.rep("  ", depth)) or ""
  local closing_indent = options.pretty and ("\n" .. string.rep("  ", depth - 1)) or ""

  if is_array(value) then
    if #value == 0 then
      return "[]"
    end
    local parts = {}
    for index = 1, #value do
      parts[index] = indent .. write_value(value[index], options, depth + 1)
    end
    return "[" .. table.concat(parts, ",") .. closing_indent .. "]"
  end

  local keys = ordered_keys(value, options.canonical)
  if #keys == 0 then
    return "{}"
  end
  local parts = {}
  for index, key in ipairs(keys) do
    local rendered_key = type(key) == "number" and ('"' .. number_to_string(key) .. '"') or ('"' .. escape_string(key) .. '"')
    parts[index] = indent .. rendered_key .. (options.pretty and ": " or ":") .. write_value(value[key], options, depth + 1)
  end
  return "{" .. table.concat(parts, ",") .. closing_indent .. "}"
end

write_value = function(value, options, depth)
  local kind = type(value)
  if value == nil or value == decode.null then
    return "null"
  elseif kind == "boolean" then
    return tostring(value)
  elseif kind == "number" then
    return number_to_string(value)
  elseif kind == "string" then
    return '"' .. escape_string(value) .. '"'
  elseif kind == "table" then
    return write_table(value, options, depth)
  end
  error("cannot serialise a " .. kind, 0)
end

--- Serialises a value. Options: `pretty` (two-space indent) and `canonical`
--- (sorted object keys).
function M.encode(value, options)
  local settings = options or {}
  return write_value(value, { pretty = settings.pretty or false, canonical = settings.canonical or false }, 1)
end

M.number_to_string = number_to_string

--- Marks a table as a JSON object, so an empty one encodes as `{}` rather than
--- `[]`. Decoding already returns tagged empty objects.
function M.object(value)
  return setmetatable(value or {}, decode.object_marker)
end
M.is_array = is_array

return M
