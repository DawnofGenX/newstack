import { test } from "node:test";
import assert from "node:assert/strict";
import { diffLines, hunks, unifiedDiff } from "../src/diff.js";

test("identical input has no hunks", () => {
  assert.equal(unifiedDiff("a\nb\n", "a\nb\n"), "");
});

test("diffLines marks every operation", () => {
  const ops = diffLines("a\nb\n", "a\nc\n");
  assert.deepEqual(ops.map((op) => op.op + op.line), [" a", "-b", "+c"]);
});

test("insert in the middle", () => {
  const out = unifiedDiff("one\ntwo\n", "one\nmid\ntwo\n");
  assert.match(out, /^--- /);
  assert.match(out, /\+mid/);
  assert.match(out, /@@ -1,2 \+1,3 @@/);
});

test("delete a line", () => {
  const out = unifiedDiff("keep\ndrop\nkeep2\n", "keep\nkeep2\n");
  assert.match(out, /-drop/);
});

test("hunk header counts both sides", () => {
  const out = unifiedDiff("a\nb\nc\nd\ne\n", "a\nb\nC\nd\ne\n");
  const header = out.split("\n").find((line) => line.startsWith("@@"));
  assert.equal(header, "@@ -1,5 +1,5 @@");
});

test("distant changes produce two hunks", () => {
  const oldText = `${Array.from({ length: 20 }, (_, i) => `line${i}`).join("\n")}\n`;
  const newText = oldText.replace("line1\n", "LINE1\n").replace("line18\n", "LINE18\n");
  assert.equal(hunks(diffLines(oldText, newText), 3).length, 2);
});
