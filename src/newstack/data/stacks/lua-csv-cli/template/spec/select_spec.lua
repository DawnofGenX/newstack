local harness = require("spec.harness")
local selector = require("csval.select")

local eq = harness.eq

local ROWS = {
  { "id", "name", "amount" },
  { "1", "alpha", "10" },
  { "2", "beta", "20" },
}

harness.describe("select", function()
  harness.it("the first row is the header", function()
    eq(selector.headers(ROWS), { "id", "name", "amount" })
  end)

  harness.it("the body drops the header", function()
    eq(#selector.body(ROWS, true), 2)
    eq(#selector.body(ROWS, false), 3)
  end)

  harness.it("names resolve to 1-based positions", function()
    eq(selector.resolve("name,amount", ROWS[1], 3), { 2, 3 })
  end)

  harness.it("positions resolve when no name matches", function()
    eq(selector.resolve("3,1", ROWS[1], 3), { 3, 1 })
  end)

  harness.it("no spec keeps every column in order", function()
    eq(selector.resolve(nil, ROWS[1], 3), { 1, 2, 3 })
  end)

  harness.it("an unknown column names itself in the error", function()
    local ok, err = pcall(selector.resolve, "nope", ROWS[1], 3)
    eq(ok, false, "ok")
    harness.contains(err, "unknown column 'nope'", "error")
  end)

  harness.it("a position past the width is an unknown column", function()
    local ok, err = pcall(selector.resolve, "9", nil, 3)
    eq(ok, false, "ok")
    harness.contains(err, "unknown column '9'", "error")
  end)

  harness.it("projection keeps the requested order", function()
    eq(selector.project({ { "1", "alpha", "10" } }, { 3, 1 }), { { "10", "1" } })
  end)

  harness.it("splitting trims spaces and drops empties", function()
    eq(selector.split(" a , b ,,"), { "a", "b" })
  end)

  harness.it("objects are keyed by header name", function()
    local objects = selector.as_objects({ "id", "name" }, { { "1", "alpha" } })
    eq(objects[1].id, "1")
    eq(objects[1].name, "alpha")
  end)
end)
