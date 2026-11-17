import { test } from "node:test";
import assert from "node:assert/strict";
import { greet, add } from "../src/cli.js";

test("greet", () => {
  assert.equal(greet("world"), "Hello, world!");
});

test("add", () => {
  assert.equal(add("2", "3"), 5);
});