-- Public surface of the ljson module: parse, serialise, and the argv parser
-- the CLI needs. Nothing here touches stdio.

local decode = require("ljson.decode")
local encode = require("ljson.encode")

local M = {}

M.version = "0.1.0"
M.null = decode.null
M.parse = decode.parse
M.encode = encode.encode
M.number_to_string = encode.number_to_string
M.object = encode.object

function M.usage(program)
  return table.concat({
    "Usage: " .. program .. " [options] [FILE]",
    "",
    "Reads JSON from FILE (or standard input), validates it, and prints it",
    "back either compact, pretty-printed, or canonicalised.",
    "",
    "Options:",
    "  --pretty      two-space indentation",
    "  --compact     no spaces at all (the default)",
    "  --canonical   sort object keys so equal documents print identically",
    "  --get PATH    print one value, e.g. --get user.name or --get items[0].id",
    "  --check       validate only; prints 'valid' or reports the error",
    "  -h, --help    show this help and exit",
    "  -V, --version print the version and exit",
    "",
    "Exit codes:",
    "  0  success (or --help/--version, or a valid document with --check)",
    "  1  the input is not valid JSON, or PATH does not exist",
    "  2  usage error",
    "",
  }, "\n")
end

--- Splits a path like `user.items[0].id` into {"user", "items", 1, "id"}.
function M.split_path(path)
  local parts = {}
  for piece in path:gmatch("[^%.]+") do
    local bracket = piece:find("%[")
    local name = bracket and piece:sub(1, bracket - 1) or piece
    if name ~= "" then
      parts[#parts + 1] = name
    end
    if bracket then
      local digits = piece:match("%[(%d+)%]$")
      if not digits then
        return nil, "invalid index in path: " .. piece
      end
      parts[#parts + 1] = tonumber(digits)
    end
  end
  if #parts == 0 then
    return nil, "empty path"
  end
  return parts
end

--- Walks `value` along `parts`, returning the found value or nil plus an error.
function M.get_path(value, parts)
  local current = value
  for _, part in ipairs(parts) do
    if type(current) ~= "table" then
      return nil, "cannot index a " .. type(current)
    end
    -- Paths use JSON's 0-based indexes; Lua tables are 1-based.
    local key = type(part) == "number" and part + 1 or part
    current = current[key]
    if current == nil then
      return nil, "no value at '" .. tostring(part) .. "'"
    end
  end
  return current
end

--- Parses argv into a table: {status = "ok"|"help"|"version"|"usage", ...}.
function M.parse_options(argv)
  local options = { status = "ok", pretty = false, canonical = false, check = false, get = nil, files = {} }
  local index = 1
  local after_double_dash = false

  while index <= #argv do
    local argument = argv[index]
    index = index + 1

    if not after_double_dash and argument == "--" then
      after_double_dash = true
    elseif not after_double_dash and argument:sub(1, 1) == "-" and #argument > 1 then
      if argument == "-h" or argument == "--help" then
        options.status = "help"
        return options
      elseif argument == "-V" or argument == "--version" then
        options.status = "version"
        return options
      elseif argument == "--pretty" then
        options.pretty = true
      elseif argument == "--compact" then
        options.pretty = false
      elseif argument == "--canonical" then
        options.canonical = true
      elseif argument == "--check" then
        options.check = true
      elseif argument == "--get" then
        if index > #argv then
          options.status = "usage"
          options.message = "--get needs a path"
          return options
        end
        options.get = argv[index]
        index = index + 1
      else
        options.status = "usage"
        options.message = "unknown option: " .. argument
        return options
      end
    else
      options.files[#options.files + 1] = argument
    end
  end

  if #options.files > 1 then
    options.status = "usage"
    options.message = "expected at most one file"
  end
  return options
end

return M
