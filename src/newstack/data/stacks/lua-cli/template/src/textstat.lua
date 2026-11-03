--! Module facade: `require("textstat")` with LUA_PATH="src/?.lua;src/?/init.lua".
--!
--! Counting and parsing stay in their own files so each can be tested alone;
--! this table only re-exports them plus the shipped version.

local counts = require("textstat.counts")
local options = require("textstat.options")

return {
  count = counts.count,
  add = counts.add,
  parse = options.parse,
  usage = options.usage,
  version = options.version,
}
