import { assertEquals, assertThrows } from "./asserts.ts";
import { DiffError, diffLines, formatStats, hunks, stats, toLines, unifiedBody, words } from "../src/diff.ts";

Deno.test("toLines drops the phantom line after a final newline", () => {
  assertEquals(toLines("a\nb\n"), ["a", "b"]);
  assertEquals(toLines("a\nb"), ["a", "b"]);
  assertEquals(toLines(""), []);
  assertEquals(toLines("\n"), [""]);
});

Deno.test("identical inputs produce only context lines", () => {
  const ops = diffLines(["a", "b"], ["a", "b"]);
  assertEquals(ops.map((line) => line.op), [" ", " "]);
  assertEquals(stats(ops).changed, false);
});

Deno.test("a replaced line is a deletion followed by an addition", () => {
  const ops = diffLines(["a", "b", "c"], ["a", "x", "c"]);
  assertEquals(ops.map((line) => `${line.op}${line.text}`), [" a", "-b", "+x", " c"]);
  assertEquals(stats(ops), { added: 1, removed: 1, changed: true });
});

Deno.test("line numbers follow each side", () => {
  const ops = diffLines(["a", "b"], ["a", "b", "c"]);
  assertEquals(ops.map((line) => [line.left, line.right]), [[1, 1], [2, 2], [null, 3]]);
});

Deno.test("pure insertion keeps both sides consistent", () => {
  const ops = diffLines([], ["one", "two"]);
  assertEquals(ops.map((line) => `${line.op}${line.text}`), ["+one", "+two"]);
  assertEquals(stats(ops).added, 2);
});

Deno.test("hunks carry three lines of context by default shape", () => {
  const left = Array.from({ length: 10 }, (_, index) => `l${index}`);
  const right = [...left];
  right[5] = "changed";
  const body = unifiedBody(diffLines(left, right), 1);
  assertEquals(body[0], "@@ -5,3 +5,3 @@");
  assertEquals(body.slice(1), [" l4", "-l5", "+changed", " l6"]);
});

Deno.test("two nearby changes merge into one hunk", () => {
  const left = ["a", "b", "c", "d", "e"];
  const right = ["a", "B", "c", "D", "e"];
  const merged = hunks(diffLines(left, right), 1);
  assertEquals(merged.length, 1);
  assertEquals(hunks(diffLines(left, right), 0).length, 2);
});

Deno.test("an adjacent replacement stays in one hunk even with zero context", () => {
  const body = unifiedBody(diffLines(["a", "b"], ["a", "c"]), 0);
  assertEquals(body[0], "@@ -2 +2 @@");
  assertEquals(body.slice(1), ["-b", "+c"]);
});

Deno.test("a deletion-only hunk points at the line it followed", () => {
  const body = unifiedBody(diffLines(["a", "b", "c"], ["a", "c"]), 0);
  assertEquals(body[0], "@@ -2 +1,0 @@");
  assertEquals(body.slice(1), ["-b"]);
});

Deno.test("deleting every line reports an empty right range", () => {
  const body = unifiedBody(diffLines(["a"], []), 0);
  assertEquals(body[0], "@@ -1 +0,0 @@");
});

Deno.test("negative context is refused", () => {
  assertThrows(() => hunks([{ op: "-", text: "x", left: 1, right: null }], -1), DiffError);
});

Deno.test("formatStats summarises counts", () => {
  assertEquals(formatStats("a -> b", { added: 2, removed: 1, changed: true }), "a -> b: 2 insertion(s), 1 deletion(s), 3 change(s)");
  assertEquals(formatStats("a -> a", { added: 0, removed: 0, changed: false }), "a -> a: no changes");
});

Deno.test("words keeps whitespace as tokens", () => {
  assertEquals(words("a b  c"), ["a", " ", "b", "  ", "c"]);
});
