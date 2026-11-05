import assert from "node:assert/strict";
import test from "node:test";
import { add, countBytes, Counter, ZERO } from "../src/{{ package_name }}/count.js";

const utf8 = (text: string) => new TextEncoder().encode(text);

function feed(...chunks: Uint8Array[]) {
  const counter = new Counter();
  for (const chunk of chunks) counter.push(chunk);
  return counter.end();
}

test("an empty stream counts nothing", () => {
  assert.deepEqual(countBytes(new Uint8Array()), { lines: 0, words: 0, bytes: 0 });
});

test("bytes are utf-8 bytes, not characters", () => {
  const counts = countBytes(utf8("héllo\n"));
  assert.equal(counts.bytes, 7);
  assert.equal(counts.words, 1);
  assert.equal(counts.lines, 1);
});

test("a last line without a newline still counts as a line", () => {
  assert.equal(countBytes(utf8("a\nb")).lines, 2);
  assert.equal(countBytes(utf8("a\nb\n")).lines, 2);
  assert.equal(countBytes(utf8("a")).lines, 1);
});

test("crlf files count the same as lf files", () => {
  const crlf = countBytes(utf8("a\r\nb\r\n"));
  const lf = countBytes(utf8("a\nb\n"));
  assert.equal(crlf.lines, lf.lines);
  assert.equal(crlf.words, lf.words);
  assert.equal(crlf.bytes, lf.bytes + 2);
});

test("a character split across chunks does not become two words", () => {
  const buffer = utf8("héllo");
  assert.deepEqual(feed(buffer.slice(0, 2), buffer.slice(2)), { lines: 1, words: 1, bytes: 6 });
});

test("a word split across chunks does not become two words", () => {
  const buffer = utf8("one two");
  assert.equal(feed(buffer.slice(0, 5), buffer.slice(5)).words, 2);
});

test("whitespace-only input has no words", () => {
  assert.equal(countBytes(utf8("  \n\t\n")).words, 0);
  assert.equal(countBytes(utf8("  \n\t\n")).lines, 2);
});

test("a counter refuses misuse instead of reporting a wrong number", () => {
  const counter = new Counter();
  counter.push(utf8("x"));
  counter.end();
  assert.throws(() => counter.push(utf8("y")), /push\(\) after end\(\)/);
  assert.throws(() => counter.end(), /end\(\) twice/);
});

test("add() and ZERO agree", () => {
  assert.deepEqual(add(ZERO, { lines: 1, words: 2, bytes: 3 }), { lines: 1, words: 2, bytes: 3 });
  assert.deepEqual(add({ lines: 1, words: 2, bytes: 3 }, ZERO), { lines: 1, words: 2, bytes: 3 });
});
