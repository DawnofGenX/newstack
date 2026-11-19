-- A JSON parser in about two hundred lines: recursive descent over a string,
-- with offsets in every error message so a broken document is easy to fix.
--
-- Supported: objects, arrays, strings (including \uXXXX pairs), numbers,
-- true/false/null. Rejected: trailing data, control characters inside
-- strings, leading zeros, a leading '+', NaN/Infinity.

local M = {}

-- JSON `null` needs its own value: Lua's `nil` disappears from tables, so an
-- array of [1, null, 3] would silently become two elements.
M.null = setmetatable({}, { __tostring = function() return "null" end })

-- An empty Lua table is indistinguishable from an empty array, so an empty
-- object is tagged with this metatable and the encoder honours the tag.
M.object_marker = { __json_object = true }

local escapes = {
  ['"'] = '"', ["\\"] = "\\", ["/"] = "/", b = "\b",
  f = "\f", n = "\n", r = "\r", t = "\t",
}

local function fail(problem, position, kind)
  error(string.format("%s at offset %d (%s)", problem, position, kind), 0)
end

local function utf8_encode(code)
  if code < 0x80 then
    return string.char(code)
  elseif code < 0x800 then
    return string.char(0xC0 + math.floor(code / 0x40), 0x80 + code % 0x40)
  elseif code < 0x10000 then
    return string.char(
      0xE0 + math.floor(code / 0x1000),
      0x80 + math.floor(code / 0x40) % 0x40,
      0x80 + code % 0x40
    )
  end
  return string.char(
    0xF0 + math.floor(code / 0x40000),
    0x80 + math.floor(code / 0x1000) % 0x40,
    0x80 + math.floor(code / 0x40) % 0x40,
    0x80 + code % 0x40
  )
end

local function skip_space(text, position)
  local _, stop = text:find("^[ \t\r\n]*", position)
  return stop + 1
end

local parse_value

local function parse_string(text, position)
  local start = position
  position = position + 1 -- opening quote
  local parts = {}
  while true do
    local character = text:sub(position, position)
    if character == "" then
      fail("unterminated string", start, "invalid JSON")
    elseif character == '"' then
      return table.concat(parts), position + 1
    elseif character == "\\" then
      local code = text:sub(position + 1, position + 1)
      if code == "u" then
        local hex = text:sub(position + 2, position + 5)
        if not hex:match("^%x%x%x%x$") then
          fail("invalid \\u escape", position, "invalid JSON")
        end
        local value = tonumber(hex, 16)
        position = position + 6
        if value >= 0xD800 and value <= 0xDBFF then
          local low = text:sub(position, position + 5)
          local surrogate = low:match("^\\u(%x%x%x%x)$")
          if surrogate then
            local combined = 0x10000 + (value - 0xD800) * 0x400 + (tonumber(surrogate, 16) - 0xDC00)
            parts[#parts + 1] = utf8_encode(combined)
            position = position + 6
          else
            parts[#parts + 1] = utf8_encode(value)
          end
        else
          parts[#parts + 1] = utf8_encode(value)
        end
      elseif escapes[code] then
        parts[#parts + 1] = escapes[code]
        position = position + 2
      else
        fail("invalid escape \\" .. code, position, "invalid JSON")
      end
    else
      local byte = character:byte()
      if byte < 0x20 then
        fail("control character in string", position, "invalid JSON")
      end
      parts[#parts + 1] = character
      position = position + 1
    end
  end
end

local function parse_number(text, position)
  local start = position
  local _, stop = text:find("^-?%d+%.?%d*[eE]?[-+]?%d*", position)
  if not stop then
    fail("invalid number", position, "invalid JSON")
  end
  local literal = text:sub(start, stop)
  if literal:match("^-?0%d") then
    fail("leading zero in number", position, "invalid JSON")
  end
  local value = tonumber(literal)
  if value == nil then
    fail("invalid number", position, "invalid JSON")
  end
  return value, stop + 1
end

local function parse_array(text, position)
  local out = {}
  position = skip_space(text, position + 1)
  if text:sub(position, position) == "]" then
    return out, position + 1
  end
  while true do
    local value
    value, position = parse_value(text, position)
    out[#out + 1] = value
    position = skip_space(text, position)
    local character = text:sub(position, position)
    if character == "]" then
      return out, position + 1
    elseif character == "," then
      position = skip_space(text, position + 1)
    else
      fail("expected ',' or ']'", position, "invalid JSON")
    end
  end
end

local function parse_object(text, position)
  local out = {}
  position = skip_space(text, position + 1)
  if text:sub(position, position) == "}" then
    return setmetatable(out, M.object_marker), position + 1
  end
  while true do
    if text:sub(position, position) ~= '"' then
      fail("expected a string key", position, "invalid JSON")
    end
    local key
    key, position = parse_string(text, position)
    position = skip_space(text, position)
    if text:sub(position, position) ~= ":" then
      fail("expected ':'", position, "invalid JSON")
    end
    position = skip_space(text, position + 1)
    local value
    value, position = parse_value(text, position)
    out[key] = value
    position = skip_space(text, position)
    local character = text:sub(position, position)
    if character == "}" then
      return out, position + 1
    elseif character == "," then
      position = skip_space(text, position + 1)
    else
      fail("expected ',' or '}'", position, "invalid JSON")
    end
  end
end

parse_value = function(text, position)
  position = skip_space(text, position)
  local character = text:sub(position, position)
  if character == "{" then
    return parse_object(text, position)
  elseif character == "[" then
    return parse_array(text, position)
  elseif character == '"' then
    return parse_string(text, position)
  elseif text:sub(position, position + 3) == "true" then
    return true, position + 4
  elseif text:sub(position, position + 4) == "false" then
    return false, position + 5
  elseif text:sub(position, position + 3) == "null" then
    return M.null, position + 4
  elseif character == "" then
    fail("unexpected end of input", position, "invalid JSON")
  end
  return parse_number(text, position)
end

--- Parses a JSON document. Raises a string error on malformed input.
function M.parse(text)
  local value, position = parse_value(text, 1)
  position = skip_space(text, position)
  if position <= #text then
    fail("trailing data", position, "invalid JSON")
  end
  return value
end

M.utf8_encode = utf8_encode

return M
