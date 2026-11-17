import { test } from "node:test";
import assert from "node:assert/strict";
import { Readable } from "node:stream";
import { CsvParser, parseStream, encodeField, encodeRow, objectsToCsv } from "../src/csv.js";

function streamFrom(text) {
  return Readable.from([text]);
}

test("basic csv", async () => {
  const rows = await parseStream(streamFrom("a,b\n1,2\n"));
  assert.deepEqual(rows, [["a","b"],["1","2"]]);
});

test("quoted fields and embedded newline", async () => {
  const text = 'x,y\n"a""b\nc",d\n';
  const rows = await parseStream(streamFrom(text));
  assert.deepEqual(rows, [["x","y"], ['a"b\nc', "d"]]);
});

test("crlf and trailing newline", async () => {
  const rows = await parseStream(streamFrom("a,b\r\n1,2\r\n"));
  assert.deepEqual(rows, [["a","b"],["1","2"]]);
});

test("no trailing newline", async () => {
  const rows = await parseStream(streamFrom("a,b\n1,2"));
  assert.deepEqual(rows, [["a","b"],["1","2"]]);
});

test("empty trailing line handling", async () => {
  const rows = await parseStream(streamFrom("a\n"));
  assert.deepEqual(rows, [["a"]]);
});

test("doubled quotes", async () => {
  const rows = await parseStream(streamFrom('"a""b"\n'));
  assert.deepEqual(rows, [['a"b']]);
});

test("backpressure chunks", async () => {
  const r = new Readable({ read() {} });
  const p = parseStream(r);
  // push in small chunks
  setTimeout(() => { r.push("a,"); r.push("b\n1,"); r.push("2\n"); r.push(null); }, 10);
  const rows = await p;
  assert.deepEqual(rows, [["a","b"],["1","2"]]);
});

test("encodeField", () => {
  assert.equal(encodeField('a"b\nc'), '"a""b\nc"');
  assert.equal(encodeField("plain"), "plain");
});

test("objectsToCsv roundtrip", () => {
  const csv = objectsToCsv([{name: "a", val: 1}, {name: "b,c", val: 2}]);
  assert.ok(csv.includes('"b,c"'));
});