-- Test runner: lua5.4 spec/run.lua (from the project root).

package.path = "./src/?.lua;./src/?/init.lua;./?.lua;./?/init.lua;" .. package.path

local harness = require("spec.harness")

require("spec.parse_spec")
require("spec.select_spec")
require("spec.options_spec")
require("spec.cli_spec")

harness.finish()
