import assert from "node:assert/strict";
import test from "node:test";
import type { FileCounts, Report } from "../src/{{ package_name }}/format.js";
import { renderJson, renderTable } from "../src/{{ package_name }}/format.js";

const a: FileCounts = { path: "a.txt", lines: 2, words: 3, bytes: 10 };
const b: FileCounts = { path: "b.txt", lines: 1, words: 1, bytes: 4 };
const broken: FileCounts = { path: "gone.txt", lines: 0, words: 0, bytes: 0, error: "ENOENT" };

const report: Report = {
  files: [a, b],
  total: { lines: 3, words: 4, bytes: 14 },
};

test("the table has a header and one row per file", () => {
  const lines = renderTable(report).split("\n").filter((line: string) => line !== "");
  assert.equal(lines.length, 4);
  assert.equal((lines[0] ?? "").trimEnd(), "lines words bytes");
  assert.match(lines[1] ?? "", /a\.txt$/);
});

test("numbers are right aligned inside their column", () => {
  const lines = renderTable(report).split("\n");
  const rowA = lines[1] ?? "";
  const rowB = lines[2] ?? "";
  assert.equal(rowA.indexOf("2"), rowB.indexOf("1"));
});

test("a single file gets no total row", () => {
  assert.ok(!renderTable({ files: [a], total: a }).includes("total"));
});

test("several files get a total row that adds up", () => {
  const lines = renderTable(report).split("\n");
  assert.match(lines[3] ?? "", /^\s*3\s+4\s+14\s+total$/);
});

test("an unreadable file shows ? instead of a zero it did not measure", () => {
  const table = renderTable({ files: [broken], total: broken });
  assert.match(table, /\?\s+\?\s+\?\s+gone\.txt: ENOENT/);
});

test("the json report round-trips", () => {
  assert.deepEqual(JSON.parse(renderJson(report)), report);
  assert.ok(renderJson(report).endsWith("\n"));
});
