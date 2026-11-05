import assert from "node:assert/strict";
import test from "node:test";
import { summarize } from "../src/stats.js";
import { evaluate, parseThresholds } from "../src/thresholds.js";
import type { Sample } from "../src/types.js";

function sample(index: number, latencyMs: number, status = 200): Sample {
  return { index, dueAt: 0n, latencyMs, status, ok: status >= 200 && status < 400 };
}

test("thresholds parse name=value pairs", () => {
  assert.deepEqual(parseThresholds(["p95=250", "errorRate=0.01"]), [
    { name: "p95", limit: 250 },
    { name: "errorRate", limit: 0.01 },
  ]);
});

test("a misspelled threshold name is an error, never a silent pass", () => {
  assert.throws(() => parseThresholds(["p9=250"]), /unknown threshold/);
  assert.throws(() => parseThresholds(["p95ms=250"]), /unknown threshold/);
});

test("a threshold without a number is an error", () => {
  assert.throws(() => parseThresholds(["p95"]), /name=value/);
  assert.throws(() => parseThresholds(["p95=fast"]), /non-negative number/);
  assert.throws(() => parseThresholds(["p95=-1"]), /non-negative number/);
});

test("evaluate compares each threshold to the summary", () => {
  const summary = summarize([sample(0, 10), sample(1, 20), sample(2, 30)], 0);
  const verdicts = evaluate(summary, parseThresholds(["p95=25", "p50=20", "max=30"]));
  assert.deepEqual(
    verdicts.map((verdict) => verdict.ok),
    [false, true, true],
  );
  assert.equal(verdicts[0]?.actual, 30);
});

test("evaluate refuses a name it cannot measure", () => {
  const summary = summarize([sample(0, 1)], 0);
  assert.throws(() => evaluate(summary, [{ name: "p75", limit: 1 }]), /unknown threshold/);
});

test("an error-rate gate is the default for a run with no thresholds", () => {
  const summary = summarize([sample(0, 1, 0)], 0);
  const verdicts = evaluate(summary, parseThresholds(["errorRate=0"]));
  assert.equal(verdicts[0]?.ok, false);
  assert.equal(verdicts[0]?.actual, 1);
});
