import assert from "node:assert/strict";
import test from "node:test";
import { compress, decompress, describe, isGzip, stats } from "../src/compress.js";

const TEXT = "the quick brown fox ".repeat(50);

test("round trip restores the exact bytes", () => {
  const packed = compress(Buffer.from(TEXT));
  assert.equal(decompress(packed).toString(), TEXT);
});

test("compressed output carries the gzip magic header", () => {
  const packed = compress(Buffer.from(TEXT));
  assert.ok(isGzip(packed));
  assert.equal(describe(packed).format, "gzip");
});

test("higher levels never produce bigger output on repetitive text", () => {
  const fast = compress(Buffer.from(TEXT), { level: 1 });
  const small = compress(Buffer.from(TEXT), { level: 9 });
  assert.ok(small.length <= fast.length);
});

test("repetitive text compresses below half its size", () => {
  const packed = compress(Buffer.from(TEXT), { level: 9 });
  assert.ok(packed.length < Buffer.byteLength(TEXT) / 2);
});

test("an out of range level is a RangeError", () => {
  assert.throws(() => compress(Buffer.from("x"), { level: 11 }), RangeError);
  assert.throws(() => compress(Buffer.from("x"), { level: 1.5 }), RangeError);
});

test("decompress refuses data that is not gzip", () => {
  assert.throws(() => decompress(Buffer.from("plain text")), /not gzip data/);
});

test("gzip detection needs the two magic bytes", () => {
  assert.equal(isGzip(Buffer.from([0x1f])), false);
  assert.equal(isGzip(Buffer.from([0x1f, 0x8b, 0x08])), true);
});

test("stats reports the rounded ratio and the saved bytes", () => {
  const entry = stats(1000, 250);
  assert.deepEqual(entry, { originalBytes: 1000, compressedBytes: 250, savedBytes: 750, ratio: 0.25 });
  assert.equal(stats(0, 0).ratio, 0);
  assert.equal(stats(3, 1).ratio, 0.333);
});
