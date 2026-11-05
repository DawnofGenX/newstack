local cjson = require("cjson")
local counts = require("counts")

local M = {}

local ESCAPES = {
  ['"'] = '\\"',
  ["\\"] = "\\\\",
  ["\n"] = "\\n",
  ["\r"] = "\\r",
  ["\t"] = "\\t",
  ["\b"] = "\\b",
  ["\f"] = "\\f",
}

-- JSON is hand-built rather than encoded through cjson because cjson serialises
-- tables in an unspecified key order, and the contract's key order is part of
-- what the tests (and the docs) promise.
local function json_string(value)
  local out = value:gsub('[%z\1-\31"\\]', function(char)
    local known = ESCAPES[char]
    if known then
      return known
    end
    return string.format("\\u%04x", char:byte())
  end)
  return '"' .. out .. '"'
end

local function counts_body(text, result)
  return string.format(
    '{"text":%s,"lines":%d,"words":%d,"bytes":%d}',
    json_string(text),
    result.lines,
    result.words,
    result.bytes
  )
end

local function error_body(status, code, detail)
  local body
  if detail then
    body = string.format('{"error":%s,"detail":%s}', json_string(code), json_string(detail))
  else
    body = string.format('{"error":%s}', json_string(code))
  end
  return { status = status, body = body }
end

local function percent_decode(raw)
  local plus = raw:gsub("%+", " ")
  return (plus:gsub("%%(%x%x)", function(hex)
    return string.char(tonumber(hex, 16))
  end))
end

function M.query_param(query, name)
  if not query or query == "" then
    return nil
  end
  for pair in query:gmatch("[^&]+") do
    local key, value = pair:match("^([^=]*)=(.*)$")
    if not key then
      key, value = pair, ""
    end
    if percent_decode(key) == name then
      return percent_decode(value)
    end
  end
  return nil
end

-- Returns the text field of a JSON object body: a string, or nil when the body
-- is not JSON at all, or `false` when the field is missing or not a string.
local function body_text(body)
  local ok, decoded = pcall(cjson.decode, body)
  if not ok or type(decoded) ~= "table" then
    return nil
  end
  local value = decoded.text
  if type(value) ~= "string" then
    return false
  end
  return value
end

function M.route(method, path, query, body)
  if method == "GET" and path == "/health" then
    return { status = 200, body = '{"status":"ok"}' }
  end
  if method == "GET" and path == "/stats" then
    local text = M.query_param(query, "text")
    if text == nil then
      return error_body(422, "missing_text")
    end
    return { status = 200, body = counts_body(text, counts.count_text(text)) }
  end
  if method == "POST" and path == "/stats" then
    local text = body_text(body or "")
    if text == nil then
      return error_body(422, "invalid_json")
    end
    if text == false then
      return error_body(422, "missing_text")
    end
    return { status = 200, body = counts_body(text, counts.count_text(text)) }
  end
  if path == "/health" or path == "/stats" then
    return error_body(405, "method_not_allowed")
  end
  return error_body(404, "not_found", string.format("no route for %s %s", method, path))
end

return M
