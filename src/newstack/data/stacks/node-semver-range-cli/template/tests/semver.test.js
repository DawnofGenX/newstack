import { test } from "node:test";
import assert from "node:assert/strict";
import { parse, compare, satisfies } from "../src/semver.js";

test("parse splits", () => {
  assert.deepEqual(parse("1.2.3"), { major: 1, minor: 2, patch: 3, prerelease: [], raw: "1.2.3" });
});

test("compare", () => {
  assert.equal(compare("1.2.3", "1.2.4"), -1);
  assert.equal(compare("2.0.0", "1.9.9"), 1);
  assert.equal(compare("1.0.0", "1.0.0"), 0);
});

test("caret", () => {
  assert.equal(satisfies("1.2.3", "^1.0.0"), true);
  assert.equal(satisfies("2.0.0", "^1.0.0"), false);
});

test("tilde", () => {
  assert.equal(satisfies("1.2.3", "~1.2.0"), true);
  assert.equal(satisfies("1.3.0", "~1.2.0"), false);
});

test("gte lte", () => {
  assert.equal(satisfies("1.5.0", ">=1.0.0"), true);
  assert.equal(satisfies("0.9.0", ">=1.0.0"), false);
  assert.equal(satisfies("1.0.0", "<=1.0.0"), true);
});

test("exact", () => {
  assert.equal(satisfies("1.2.3", "1.2.3"), true);
  assert.equal(satisfies("1.2.4", "1.2.3"), false);
});

test("hyphen", () => {
  assert.equal(satisfies("1.5.0", "1.0.0 - 2.0.0"), true);
  assert.equal(satisfies("2.5.0", "1.0.0 - 2.0.0"), false);
});
