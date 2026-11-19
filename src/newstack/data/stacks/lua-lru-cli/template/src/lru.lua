--! Module facade.
local cache = require("lru.cache")
return {
  new = cache.new,
  put = cache.put,
  get = cache.get,
  stats = cache.stats,
}