--! Command line parsing: argv in, an options table out. No printing, no
--! os.exit, so every branch is a unit test rather than a subprocess.

local M = {}

M.version = "0.1.0"

local MODES = {
  ["-l"] = "lines",
  ["--lines"] = "lines",
  ["-w"] = "words",
  ["--words"] = "words",
  ["-c"] = "bytes",
  ["--bytes"] = "bytes",
}

--- The help text. The caller passes the program name so the usage line names
--- the binary that is actually being run.
---
--- @param program string
--- @return string
function M.usage(program)
  return table.concat({
    "usage: " .. program .. " [-l | -w | -c] [--] [FILE ...]",
    "",
    "Count lines, words and bytes in each FILE, or in standard input",
    "when no FILE is given. With more than one FILE a total is printed.",
    "",
    "  -l, --lines     print the line count only",
    "  -w, --words     print the word count only",
    "  -c, --bytes     print the byte count only",
    "  -h, --help      show this help and exit",
    "  -V, --version   show the version and exit",
  }, "\n") .. "\n"
end

--- Parses an argv array (without the program name).
---
--- Hand-rolled on purpose: twenty lines of explicit loop keep `--`, a bare `-`
--- and conflicting modes obvious, and every branch below is pinned by a test.
---
--- @param args table|nil
--- @return table options {mode, help, version, files, status, message}
function M.parse(args)
  local options = {
    mode = "all",
    help = false,
    version = false,
    files = {},
    status = "ok",
    message = "",
  }

  local function usage_error(message)
    options.status = "usage"
    options.message = message
    return options
  end

  local chosen = false
  local options_ended = false

  for _, value in ipairs(args or {}) do
    if options_ended or value == "" or value == "-" then
      options.files[#options.files + 1] = value
    elseif value == "--" then
      options_ended = true
    elseif value == "-h" or value == "--help" then
      options.help = true
      options.status = "help"
      return options
    elseif value == "-V" or value == "--version" then
      options.version = true
      options.status = "version"
      return options
    else
      local mode = MODES[value]
      if mode then
        if chosen and options.mode ~= mode then
          return usage_error(
            "choose one of -l, -w, -c: '" .. value .. "' conflicts with an earlier mode"
          )
        end
        chosen = true
        options.mode = mode
      elseif value:sub(1, 1) == "-" then
        return usage_error("unknown option '" .. value .. "'")
      else
        options.files[#options.files + 1] = value
      end
    end
  end

  return options
end

return M
