local M = {}

-- Counts a UTF-8 Lua string the way `wc` does: lines end at "\n", a word is a
-- maximal run of non-whitespace bytes, and the byte count is the raw length.
-- Lua strings are byte strings, so counting bytes is just #text.
local function is_space(byte)
  return byte == 32 or byte == 9 or byte == 10 or byte == 13 or byte == 11 or byte == 12
end

function M.count_text(text)
  if type(text) ~= "string" then
    error("count_text expects a string, got " .. type(text), 2)
  end
  local lines, words = 0, 0
  local in_word = false
  for i = 1, #text do
    local byte = text:byte(i)
    if byte == 10 then
      lines = lines + 1
    end
    if is_space(byte) then
      in_word = false
    elseif not in_word then
      in_word = true
      words = words + 1
    end
  end
  return { lines = lines, words = words, bytes = #text }
end

return M
