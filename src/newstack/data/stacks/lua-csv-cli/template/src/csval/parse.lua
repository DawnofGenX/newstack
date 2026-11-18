--! Pure CSV parsing: text in, rows out. No I/O and no globals, so the specs
--! drive every branch of the state machine directly.

local M = {}

--- Raises with the source line number, which is what a user needs to fix a file.
local function fail(line, message)
  error(string.format("line %d: %s", line, message), 0)
end

--- Parses RFC 4180 CSV into a list of rows, each row a list of string fields.
---
--- Doubled quotes inside a quoted field become one quote, a delimiter inside
--- quotes is data, and CRLF outside quotes ends a row. Blank final lines are
--- not rows: "a,b\n" is one row, not two.
---
--- @param text string
--- @param delimiter string|nil single-byte delimiter, default ","
--- @return table rows
function M.parse(text, delimiter)
  delimiter = delimiter or ","
  if type(text) ~= "string" then
    text = ""
  end
  if #delimiter ~= 1 then
    error("delimiter must be a single byte", 0)
  end

  local rows, row, field = {}, {}, {}
  local quoted = false
  local quote_line = 1
  local line = 1
  local index, length = 1, #text

  while index <= length do
    local char = text:sub(index, index)
    if quoted then
      if char == '"' then
        if text:sub(index + 1, index + 1) == '"' then
          field[#field + 1] = '"'
          index = index + 2
        else
          quoted = false
          index = index + 1
        end
      else
        if char == "\n" then
          line = line + 1
        end
        field[#field + 1] = char
        index = index + 1
      end
    elseif char == '"' then
      if #field > 0 then
        fail(line, "quote inside an unquoted field")
      end
      quoted = true
      quote_line = line
      index = index + 1
    elseif char == delimiter then
      row[#row + 1] = table.concat(field)
      field = {}
      index = index + 1
    elseif char == "\r" then
      index = index + 1
    elseif char == "\n" then
      row[#row + 1] = table.concat(field)
      rows[#rows + 1] = row
      row, field = {}, {}
      line = line + 1
      index = index + 1
    else
      field[#field + 1] = char
      index = index + 1
    end
  end

  if quoted then
    fail(quote_line, "unterminated quoted field")
  end

  if #field > 0 or #row > 0 then
    row[#row + 1] = table.concat(field)
    rows[#rows + 1] = row
  end

  return rows
end

--- Raises when rows disagree about their width; the message names both widths.
---
--- A ragged file is a parse problem, not an empty column: reporting it once here
--- keeps the selector from silently filling holes with nil.
---
--- @param rows table
function M.check_rectangular(rows)
  if #rows == 0 then
    return
  end
  local width = #rows[1]
  for number, row in ipairs(rows) do
    if #row ~= width then
      fail(number, string.format("%d field(s), expected %d", #row, width))
    end
  end
end

return M
