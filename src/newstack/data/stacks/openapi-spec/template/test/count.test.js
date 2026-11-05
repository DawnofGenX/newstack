import assert from "node:assert/strict";
import { test } from "node:test";

import { countText } from "../src/count.js";

test("counts a single line", () => {
  assert.deepEqual(countText("hello world\n"), { lines: 1, words: 2, bytes: 12 });
});

test("counts nothing in an empty string", () => {
  assert.deepEqual(countText(""), { lines: 0, words: 0, bytes: 0 });
});

test("does not count a trailing partial line as a line", () => {
  assert.deepEqual(countText("abc"), { lines: 0, words: 1, bytes: 3 });
});

test("keeps blank lines in the line count", () => {
  assert.deepEqual(countText("\n\nx\n"), { lines: 3, words: 1, bytes: 4 });
});

test("counts whitespace as bytes but not as words", () => {
  assert.deepEqual(countText("  \t "), { lines: 0, words: 0, bytes: 4 });
});

test("counts UTF-8 bytes, not characters", () => {
  assert.deepEqual(countText("héllo wörld\n"), { lines: 1, words: 2, bytes: 14 });
});

test("rejects a non-string", () => {
  assert.throws(() => countText(42), TypeError);
});
