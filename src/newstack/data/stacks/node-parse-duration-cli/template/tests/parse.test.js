import { test } from "node:test";
import assert from "node:assert/strict";
import { parseDuration } from "../src/parse.js";

test("compound", () => assert.equal(parseDuration("1h30m"), 5400000));
test("days", () => assert.equal(parseDuration("2d"), 172800000));
test("ms", () => assert.equal(parseDuration("500ms"), 500));
test("weeks", () => assert.equal(parseDuration("1w2d"), 777600000));
test("throws on garbage", () => {
  assert.throws(() => parseDuration("abc"), /invalid/);
});