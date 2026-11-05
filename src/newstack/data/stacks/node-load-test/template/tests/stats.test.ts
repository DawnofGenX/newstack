import assert from "node:assert/strict";
import test from "node:test";
import { percentile, summarize } from "../src/stats.js";
import type { Sample } from "../src/types.js";

function sample(index: number, latencyMs: number, status = 200): Sample {
  return { index, dueAt: 0n, latencyMs, status, ok: status >= 200 && status < 400 };
}

const HUNDRED = Array.from({ length: 100 }, (_, index) => index + 1);

test("percentile uses nearest-rank, so every answer is a real sample", () => {
  assert.equal(percentile(HUNDRED, 95), 95);
  assert.equal(percentile(HUNDRED, 50), 50);
  assert.equal(percentile(HUNDRED, 99), 99);
  assert.equal(percentile(HUNDRED, 100), 100);
  assert.equal(percentile(HUNDRED, 1), 1);
  // Linear interpolation would say 95.05, a latency that never happened.
  assert.notEqual(percentile(HUNDRED, 95), 95.05);
});

test("percentile rejects nonsense instead of guessing", () => {
  assert.throws(() => percentile(HUNDRED, 0), /must be in/);
  assert.throws(() => percentile(HUNDRED, 101), /must be in/);
  assert.throws(() => percentile([], 50), /empty/);
});

test("summarize drops the warm-up and keeps the count honest", () => {
  const samples = Array.from({ length: 10 }, (_, index) => sample(index, 100 + index));
  const summary = summarize(samples, 3);
  assert.equal(summary.count, 7);
  assert.equal(summary.warmup, 3);
  assert.equal(summary.min, 103);
  assert.equal(summary.max, 109);
  assert.equal(summary.method, "nearest-rank");
});

test("summarize sorts by index, so arrival order does not matter", () => {
  const summary = summarize([sample(2, 30), sample(0, 10), sample(1, 20)], 0);
  assert.equal(summary.p50, 20);
  assert.equal(summary.p99, 30);
});

test("errors are counted per sample and by status", () => {
  const samples = [
    sample(0, 1),
    sample(1, 1, 0),
    sample(2, 1, 503),
    sample(3, 1),
    sample(4, 1),
  ];
  const summary = summarize(samples, 0);
  assert.equal(summary.errors, 2);
  assert.equal(summary.errorRate, 0.4);
  assert.equal(summary.statuses.error, 1);
  assert.equal(summary.statuses["503"], 1);
  assert.equal(summary.statuses["200"], 3);
});

test("a run that is all warm-up fails loudly", () => {
  assert.throws(() => summarize([sample(0, 1)], 1), /no measured samples/);
});

test("a negative warm-up is refused", () => {
  assert.throws(() => summarize([sample(0, 1)], -1), /warmup must be/);
});
