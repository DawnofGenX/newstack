import assert from "node:assert/strict";
import test from "node:test";

import { run } from "../src/pipeline.js";
import { CHUNK_BYTES, chunkSeries, kib } from "../src/types.js";

const CHUNKS = 32;
const OPTIONS = { highWaterMark: CHUNK_BYTES, latencyMs: 1 };
const series = chunkSeries(CHUNKS);
const total = CHUNKS * CHUNK_BYTES;

test("every producer delivers every byte", async () => {
  for (const mode of ["ignoring", "awaiting", "honoring", "pipeline"] as const) {
    const measure = await run(mode, series, OPTIONS);
    assert.equal(measure.bytes, total, `${mode} delivered ${measure.bytes}`);
  }
});

test("ignoring a refusal buffers the whole series", async () => {
  const measure = await run("ignoring", series, OPTIONS);
  assert.ok(
    measure.peakBuffered > 20 * CHUNK_BYTES,
    `peak was ${kib(measure.peakBuffered)}`,
  );
  assert.equal(measure.waits, 0);
});

test("awaiting an already-kept promise is not backpressure", async () => {
  const awaiting = await run("awaiting", series, OPTIONS);
  assert.ok(awaiting.peakBuffered > 20 * CHUNK_BYTES, `peak ${kib(awaiting.peakBuffered)}`);
});

test("honoring drain keeps the buffer near one chunk", async () => {
  const honoring = await run("honoring", series, OPTIONS);
  assert.ok(
    honoring.peakBuffered <= 2 * CHUNK_BYTES,
    `peak ${kib(honoring.peakBuffered)} (${honoring.peakBuffered} bytes)`,
  );
  assert.ok(honoring.waits >= 1, "it never waited");
});

test("pipeline keeps the buffer near one chunk without manual wiring", async () => {
  const piped = await run("pipeline", series, OPTIONS);
  assert.ok(piped.peakBuffered <= 2 * CHUNK_BYTES, `peak ${kib(piped.peakBuffered)}`);
});

test("waiting for drain costs no wall time when the sink is the bottleneck", async () => {
  const ignoring = await run("ignoring", series, OPTIONS);
  const honoring = await run("honoring", series, OPTIONS);
  assert.ok(
    honoring.ms <= ignoring.ms + 250,
    `honoring ${honoring.ms} ms vs ignoring ${ignoring.ms} ms`,
  );
});

test("an empty series still reports one sink lifetime", async () => {
  const measure = await run("honoring", [], OPTIONS);
  assert.equal(measure.chunks, 0);
  assert.equal(measure.bytes, 0);
  assert.equal(measure.waits, 0);
});
