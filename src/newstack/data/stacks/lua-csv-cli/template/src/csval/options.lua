--! Command line parsing: argv in, an options table out. No printing, no
--! os.exit, so every branch is a unit test rather than a subprocess.

local M = {}

M.version = "0.1.0"

--- The help text; the caller passes the program name it is actually running.
function M.usage(program)
  return table.concat({
    "usage: " .. program .. " [options] [FILE]",
    "",
    "Read delimited text from FILE (or standard input), select columns and",
    "write it back out as CSV, TSV or JSON.",
    "",
    "  -c, --columns LIST   comma-separated column names or 1-based positions",
    "  -d, --delimiter CHAR input delimiter: a single byte, or 'tab' (default ,)",
    "  -o, --output FORMAT  csv, tsv or json (default csv)",
    "      --no-header      treat the first row as data, not as column names",
    "  -h, --help           show this help and exit",
    "  -V, --version        show the version and exit",
  }, "\n") .. "\n"
end

local OUTPUTS = { csv = true, tsv = true, json = true }

local function delimiter_of(value)
  if value == "tab" or value == "\\t" then
    return "\t"
  end
  if #value ~= 1 then
    return nil
  end
  return value
end

--- Parses an argv array (without the program name).
function M.parse(args)
  local options = {
    columns = nil,
    delimiter = ",",
    output = "csv",
    header = true,
    files = {},
    status = "ok",
    message = "",
  }

  local function usage_error(message)
    options.status = "usage"
    options.message = message
    return options
  end

  local values = args or {}
  local index = 1
  local options_ended = false

  while index <= #values do
    local value = values[index]
    if options_ended or value == "-" or value == "" then
      options.files[#options.files + 1] = value
      index = index + 1
    elseif value == "--" then
      options_ended = true
      index = index + 1
    elseif value == "-h" or value == "--help" then
      options.status = "help"
      return options
    elseif value == "-V" or value == "--version" then
      options.status = "version"
      return options
    elseif value == "--no-header" then
      options.header = false
      index = index + 1
    elseif value == "-c" or value == "--columns" then
      if values[index + 1] == nil then
        return usage_error("option '" .. value .. "' needs a value")
      end
      options.columns = values[index + 1]
      index = index + 2
    elseif value:sub(1, 10) == "--columns=" then
      options.columns = value:sub(11)
      index = index + 1
    elseif value == "-d" or value == "--delimiter" then
      if values[index + 1] == nil then
        return usage_error("option '" .. value .. "' needs a value")
      end
      local delimiter = delimiter_of(values[index + 1])
      if delimiter == nil then
        return usage_error("delimiter must be a single byte or 'tab'")
      end
      options.delimiter = delimiter
      index = index + 2
    elseif value == "-o" or value == "--output" then
      if values[index + 1] == nil then
        return usage_error("option '" .. value .. "' needs a value")
      end
      if not OUTPUTS[values[index + 1]] then
        return usage_error("output must be csv, tsv or json")
      end
      options.output = values[index + 1]
      index = index + 2
    elseif value:sub(1, 1) == "-" then
      return usage_error("unknown option '" .. value .. "'")
    else
      options.files[#options.files + 1] = value
      index = index + 1
    end
  end

  return options
end

return M
