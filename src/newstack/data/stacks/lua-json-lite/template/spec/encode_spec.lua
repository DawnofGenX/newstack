local harness = require("spec.harness")
local ljson = require("ljson")
local describe, it, eq = harness.describe, harness.it, harness.eq

describe("encode", function()
  it("writes compact output by default", function()
    eq(ljson.encode({ 1, 2, 3 }), "[1,2,3]")
    eq(ljson.encode({ a = 1, b = "x" }, { canonical = true }), '{"a":1,"b":"x"}')
    eq(ljson.encode({}), "[]", "an empty table is an empty array")
    eq(ljson.encode(ljson.object({})), "{}", "tagged tables are objects")
    eq(ljson.encode(ljson.parse("{}")), "{}", "decoded empty objects stay objects")
    eq(ljson.encode({ 1 }), "[1]")
  end)

  it("writes integral numbers without a fraction", function()
    eq(ljson.encode(1.0), "1")
    eq(ljson.encode(-0.5), "-0.5")
  end)

  it("escapes strings", function()
    eq(ljson.encode('a"b\\c'), '"a\\"b\\\\c"')
    eq(ljson.encode("\n"), '"\\n"')
  end)

  it("pretty-prints with two spaces", function()
    eq(ljson.encode({ a = { 1, 2 } }, { pretty = true }), '{\n  "a": [\n    1,\n    2\n  ]\n}')
  end)

  it("sorts keys when canonical", function()
    eq(ljson.encode({ b = 1, a = 2 }, { canonical = true }), '{"a":2,"b":1}')
  end)

  it("round trips through parse", function()
    local text = '{"z":[1,2,{"y":null}],"a":"x"}'
    eq(ljson.encode(ljson.parse(text), { canonical = true }), '{"a":"x","z":[1,2,{"y":null}]}')
  end)

  it("refuses NaN", function()
    local ok = pcall(ljson.encode, 0 / 0)
    eq(ok, false)
  end)
end)
