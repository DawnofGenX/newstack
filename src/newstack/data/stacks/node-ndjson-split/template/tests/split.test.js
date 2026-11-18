import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { parseNdjson, splitRecords, serialize, partName } from "../src/split.js";

const TEXT = '{"id":1}\n\n{"id":2}\n{"id":3}\n';

test("parses records and skips blank lines", () => {
  assert.deepEqual(parseNdjson(TEXT), [{ id: 1 }, { id: 2 }, { id: 3 }]);
});

test("reports the line number of invalid json", () => {
  assert.throws(() => parseNdjson('{"id":1}\nnot json\n'), /invalid json on line 2/);
});

test("serialize roundtrips", () => {
  const records = parseNdjson(TEXT);
  assert.equal(serialize(records), '{"id":1}\n{"id":2}\n{"id":3}\n');
  assert.equal(serialize([]), "");
});

test("splits by line count", () => {
  const chunks = splitRecords(parseNdjson(TEXT), { maxLines: 2 });
  assert.deepEqual(chunks.map((c) => c.length), [2, 1]);
});

test("splits by byte budget", () => {
  const records = [{ pad: "x".repeat(40) }, { pad: "y".repeat(40) }, { pad: "z".repeat(40) }];
  const chunks = splitRecords(records, { maxBytes: 60 });
  assert.equal(chunks.length, 3);
  for (const chunk of chunks) assert.ok(Buffer.byteLength(serialize(chunk)) <= 60);
});

test("rejects a record larger than the byte budget", () => {
  assert.throws(() => splitRecords([{ pad: "x".repeat(200) }], { maxBytes: 50 }), /exceeds maxBytes/);
});

test("part names are zero padded", () => {
  assert.equal(partName(1), "part-0001.ndjson");
  assert.equal(partName(42), "part-0042.ndjson");
});

test("cli writes parts and reports a summary", () => {
  const dir = mkdtempSync(join(tmpdir(), "nd-"));
  const input = join(dir, "data.ndjson");
  writeFileSync(input, TEXT);
  const out = join(dir, "parts");
  const res = spawnSync(process.execPath, ["src/cli.js", "--file", input, "--out-dir", out, "--max-lines", "2"], { encoding: "utf8" });
  assert.equal(res.status, 0, res.stderr);
  const summary = JSON.parse(res.stdout);
  assert.equal(summary.records, 3);
  assert.equal(summary.chunks, 2);
  const files = readdirSync(out).sort();
  assert.deepEqual(files, ["part-0001.ndjson", "part-0002.ndjson"]);
  assert.deepEqual(parseNdjson(readFileSync(join(out, "part-0001.ndjson"), "utf8")), [{ id: 1 }, { id: 2 }]);
  assert.deepEqual(parseNdjson(readFileSync(join(out, "part-0002.ndjson"), "utf8")), [{ id: 3 }]);
});

test("cli exits 1 on invalid json", () => {
  const dir = mkdtempSync(join(tmpdir(), "nd-"));
  const input = join(dir, "bad.ndjson");
  writeFileSync(input, "not json\n");
  const res = spawnSync(process.execPath, ["src/cli.js", "--file", input, "--out-dir", join(dir, "o")], { encoding: "utf8" });
  assert.equal(res.status, 1);
  assert.match(res.stderr, /invalid json on line 1/);
});
