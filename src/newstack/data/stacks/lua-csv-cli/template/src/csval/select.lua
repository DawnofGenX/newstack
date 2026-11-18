--! Column selection: turning names, positions and specs into indexes.

local M = {}

--- The first row, which the CLI treats as the header unless --no-header is set.
function M.headers(rows)
  return rows[1]
end

--- The rows below the header, or all rows when there is no header.
function M.body(rows, has_header)
  if has_header then
    local body = {}
    for index = 2, #rows do
      body[#body + 1] = rows[index]
    end
    return body
  end
  return rows
end

--- Maps header names to their 1-based position.
function M.index_names(headers)
  local by_name = {}
  for position, name in ipairs(headers or {}) do
    if by_name[name] == nil then
      by_name[name] = position
    end
  end
  return by_name
end

--- Resolves a comma-separated spec ("id,amount" or "1,3") into positions.
---
--- Names win over numbers, so a header literally called "1" is reachable by
--- name and the first column by position only when no header says otherwise.
---
--- @param spec string|nil
--- @param headers table|nil
--- @param width number
--- @return table positions
function M.resolve(spec, headers, width)
  local positions = {}
  if spec == nil or spec == "" then
    for index = 1, width do
      positions[index] = index
    end
    return positions
  end

  local by_name = M.index_names(headers)
  for _, raw in ipairs(M.split(spec)) do
    local position = by_name[raw]
    if position == nil then
      local number = tonumber(raw)
      if number and number >= 1 and number <= width and math.type(number) == "integer" then
        position = number
      end
    end
    if position == nil then
      error(string.format("unknown column '%s'", raw), 0)
    end
    positions[#positions + 1] = position
  end
  return positions
end

--- Splits on commas, keeping empty pieces out and trimming spaces around names.
function M.split(spec)
  local parts = {}
  for piece in (tostring(spec) .. ","):gmatch("([^,]*),") do
    piece = piece:match("^%s*(.-)%s*$")
    if piece ~= "" then
      parts[#parts + 1] = piece
    end
  end
  return parts
end

--- Projects rows onto the given positions, preserving their order.
function M.project(rows, positions)
  local projected = {}
  for index, row in ipairs(rows) do
    local fields = {}
    for slot, position in ipairs(positions) do
      fields[slot] = row[position] or ""
    end
    projected[index] = fields
  end
  return projected
end

--- Turns rows plus a header into objects keyed by column name.
function M.as_objects(headers, rows)
  local objects = {}
  for index, row in ipairs(rows) do
    local object = {}
    for position, name in ipairs(headers) do
      object[name] = row[position] or ""
    end
    objects[index] = object
  end
  return objects
end

return M
