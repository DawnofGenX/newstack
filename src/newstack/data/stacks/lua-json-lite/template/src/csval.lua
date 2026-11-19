--! Module facade: `require("csval")` with LUA_PATH="src/?.lua;src/?/init.lua".

local parse = require("csval.parse")
local format = require("csval.format")
local select_columns = require("csval.select")
local options = require("csval.options")

return {
  parse = parse.parse,
  check_rectangular = parse.check_rectangular,
  render = format.render,
  encode = format.encode,
  headers = select_columns.headers,
  body = select_columns.body,
  resolve = select_columns.resolve,
  split = select_columns.split,
  project = select_columns.project,
  as_objects = select_columns.as_objects,
  parse_options = options.parse,
  usage = options.usage,
  version = options.version,
}
