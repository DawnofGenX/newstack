import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { parseCsv, summarize } from "../src/csv.js";

test("parses simple rows with CRLF", () => {
  const { headers, rows } = parseCsv("name,age\r\nalice,30\r\nbob,25\r\n");
  assert.deepEqual(headers, ["name", "age"]);
  assert.deepEqual(rows, [["alice", "30"], ["bob", "25"]]);
});

test("handles quoted commas, doubled quotes and newlines", () => {
  const text = 'sku,note\nA1,"says ""hi"", loudly"\nB2,"two\nlines"\n';
  const { rows } = parseCsv(text);
  assert.deepEqual(rows, [
    ["A1", 'says "hi", loudly'],
    ["B2", "two\nlines"],
  ]);
});

test("rejects ragged rows and unterminated quotes", () => {
  assert.throws(() => parseCsv("a,b\n1\n"), /row 2 has 1 fields, expected 2/);
  assert.throws(() => parseCsv('a,b\n"open,2\n'), /unterminated quoted field/);
});

test("empty input yields no headers", () => {
  assert.deepEqual(parseCsv(""), { headers: [], rows: [] });
});

test("summarize computes numeric stats and distinct counts", () => {
  const { headers, rows } = parseCsv("item,qty,note\na,2,x\nb,4,x\nc,,y\n");
  const stats = summarize(headers, rows);
  assert.equal(stats[0].column, "item");
  assert.equal(stats[0].distinct, 3);
  assert.equal(stats[1].numeric.count, 2);
  assert.equal(stats[1].numeric.mean, 3);
  assert.equal(stats[1].numeric.min, 2);
  assert.equal(stats[1].numeric.max, 4);
  assert.equal(stats[1].empty, 1);
  assert.equal(stats[2].numeric, null);
});

test("cli prints json and a table", () => {
  const dir = mkdtempSync(join(tmpdir(), "csv-"));
  const file = join(dir, "data.csv");
  writeFileSync(file, "item,qty\na,2\nb,4\n");
  const json = spawnSync(process.execPath, ["src/cli.js", "--file", file], { encoding: "utf8" });
  assert.equal(json.status, 0, json.stderr);
  const parsed = JSON.parse(json.stdout);
  assert.equal(parsed.rows, 2);
  assert.equal(parsed.columns[1].numeric.mean, 3);

  const table = spawnSync(process.execPath, ["src/cli.js", "--file", file, "--table"], { encoding: "utf8" });
  assert.equal(table.status, 0, table.stderr);
  assert.match(table.stdout, /qty/);
  assert.match(table.stdout, /mean 3/);

  const bad = join(dir, "bad.csv");
  writeFileSync(bad, "a,b\n1\n");
  const failed = spawnSync(process.execPath, ["src/cli.js", "--file", bad], { encoding: "utf8" });
  assert.equal(failed.status, 1);
  assert.match(failed.stderr, /row 2 has 1 fields/);
});
