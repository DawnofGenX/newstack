import assert from "node:assert/strict";
import test from "node:test";

import { slowSink } from "../src/sink.js";
import { CHUNK_BYTES, chunkSeries, kib, ratio } from "../src/types.js";

test("chunkSeries fills every chunk with its own byte", () => {
  const chunks = chunkSeries(4, 8);
  assert.equal(chunks.length, 4);
  assert.deepEqual(
    chunks.map((chunk) => chunk[0]),
    [0, 1, 2, 3],
  );
});

test("chunkSeries defaults to the chunk size", () => {
  const [chunk] = chunkSeries(1);
  assert.equal(chunk?.byteLength, CHUNK_BYTES);
});

test("kib is one decimal and never rounds to nothing", () => {
  assert.equal(kib(16 * 1024), "16.0 KiB");
  assert.equal(kib(1024 * 1024), "1024.0 KiB");
  assert.equal(kib(0), "0.0 KiB");
});

test("ratio names what it compares against", () => {
  assert.equal(ratio(3 * CHUNK_BYTES, CHUNK_BYTES), "3.0x a chunk");
  assert.equal(ratio(0, CHUNK_BYTES), "0.0x a chunk");
});

test("a writable with a full highWaterMark refuses the next chunk", () => {
  const sink = slowSink({ highWaterMark: CHUNK_BYTES, latencyMs: 0 });
  assert.equal(sink.stream.write(new Uint8Array(CHUNK_BYTES)), false);
  sink.stream.destroy();
});

test("a writable below its highWaterMark accepts", () => {
  const sink = slowSink({ highWaterMark: 4 * CHUNK_BYTES, latencyMs: 0 });
  assert.equal(sink.stream.write(new Uint8Array(CHUNK_BYTES)), true);
  sink.stream.destroy();
});
