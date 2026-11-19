--! Pure LRU cache: no I/O, no globals. Capacity, eviction and stats live here.
-- stack: lua-lru-cli

local M = {}

--- Creates a new cache with the given capacity.
function M.new(capacity)
  if type(capacity) ~= "number" or capacity < 1 then
    capacity = 1
  end
  return { cap = capacity, map = {}, order = {}, hits = 0, misses = 0, puts = 0 }
end

local function touch(cache, key)
  for i = 1, #cache.order do
    if cache.order[i] == key then
      table.remove(cache.order, i)
      break
    end
  end
  cache.order[#cache.order + 1] = key
end

--- Stores value under key, evicting LRU entry when full.
function M.put(cache, key, value)
  if cache.map[key] == nil and #cache.order >= cache.cap then
    local evict = table.remove(cache.order, 1)
    cache.map[evict] = nil
  end
  cache.map[key] = value
  touch(cache, key)
  cache.puts = cache.puts + 1
end

--- Returns value or nil on miss; updates recency and stats.
function M.get(cache, key)
  if cache.map[key] == nil then
    cache.misses = cache.misses + 1
    return nil
  end
  cache.hits = cache.hits + 1
  touch(cache, key)
  return cache.map[key]
end

--- Returns a stats table.
function M.stats(cache)
  return {
    size = #cache.order,
    capacity = cache.cap,
    hits = cache.hits,
    misses = cache.misses,
    puts = cache.puts,
  }
end

return M