import assert from "node:assert/strict";
import test from "node:test";
import { build, render, samplesOf } from "../src/report.js";
import { summarize } from "../src/stats.js";
import { evaluate, parseThresholds } from "../src/thresholds.js";
import type { Sample } from "../src/types.js";

function sample(index: number, latencyMs: number, ok = true): Sample {
  return { index, dueAt: 0n, latencyMs, status: ok ? 200 : 0, ok };
}

function reportOf(samples: Sample[], limits: string[]) {
  const summary = summarize(samples, 0);
  return build({
    target: "http://127.0.0.1:5471/ok",
    startedAt: "2026-11-05T00:00:00.000Z",
    requests: samples.length,
    concurrency: 2,
    warmup: 0,
    wallMs: 500,
    summary,
    thresholds: evaluate(summary, parseThresholds(limits)),
  });
}

test("the report carries provenance, not just numbers", () => {
  const report = reportOf([sample(0, 10), sample(1, 20)], ["p95=100"]);
  assert.equal(report.format, 1);
  assert.equal(report.target, "http://127.0.0.1:5471/ok");
  assert.match(report.node, /^v\d+\./);
  assert.equal(report.summary.method, "nearest-rank");
  assert.equal(report.requestsPerSecond, 4);
  assert.equal(report.passed, true);
});

test("render prints a greppable summary and the verdict", () => {
  const text = render(reportOf([sample(0, 10), sample(1, 20)], ["p95=100"]));
  assert.match(text, /^samples    2 measured, 0 warm-up, 0 errors \(0\.00%\)$/m);
  assert.match(text, /^percentile nearest-rank$/m);
  assert.match(text, /^threshold  p95       <= 100    ok 20$/m);
  assert.match(text, /^result     PASS$/m);
});

test("a failed threshold is visible in the verdict line", () => {
  const text = render(reportOf([sample(0, 10)], ["p95=5"]));
  assert.match(text, /FAILED/);
  assert.match(text, /^result     FAIL \(1 threshold\(s\)\)$/m);
});

test("samples serialise to what replay reads back", () => {
  const file = samplesOf([sample(0, 1.23456), sample(1, 2, false)]);
  assert.deepEqual(file, [
    { latencyMs: 1.235, ok: true },
    { latencyMs: 2, ok: false },
  ]);
});
