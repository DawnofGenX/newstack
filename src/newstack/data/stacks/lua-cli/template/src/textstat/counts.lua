--! Pure counting: no I/O, no globals. The entry point reads the bytes; every
--! decision about what a line, a word and a byte are lives here, so the tests
--! can drive this module directly.

local M = {}

local NEWLINE = 10
local WHITESPACE = { [32] = true, [9] = true, [13] = true, [11] = true, [12] = true }

--- Counts newlines, whitespace-separated words and raw bytes.
---
--- Lines follow `wc -l`: the number of "\n" bytes, so a final line without a
--- terminator is not counted. Words are maximal runs of non-whitespace bytes and
--- `bytes` is the length of the string, which is what `wc -c` reports. This is
--- the same contract as the other newstack CLI stacks.
---
--- @param text string
--- @return table counts {lines=number, words=number, bytes=number}
function M.count(text)
  if type(text) ~= "string" then
    text = ""
  end
  local lines, words, bytes = 0, 0, #text
  local in_word = false
  for index = 1, #text do
    local byte = string.byte(text, index)
    if byte == NEWLINE then
      lines = lines + 1
      in_word = false
    elseif WHITESPACE[byte] then
      in_word = false
    elseif not in_word then
      words = words + 1
      in_word = true
    end
  end
  return { lines = lines, words = words, bytes = bytes }
end

--- Adds two totals field by field, so several files can be reported as one.
---
--- @param left table
--- @param right table
--- @return table counts
function M.add(left, right)
  return {
    lines = left.lines + right.lines,
    words = left.words + right.words,
    bytes = left.bytes + right.bytes,
  }
end

return M
