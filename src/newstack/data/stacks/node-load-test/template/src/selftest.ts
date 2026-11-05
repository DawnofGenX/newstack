//! Offline assertions over the arithmetic and the client, no shell required.

import assert from "node:assert/strict";
import { load } from "./client.js";
import { startStub } from "./stub.js";
import { percentile, summarize } from "./stats.js";
import { evaluate, parseThresholds } from "./thresholds.js";
import { build, render, samplesOf } from "./report.js";
import type { Sample } from "./types.js";

let passed = 0;
const failures: string[] = [];

function check(name: string, body: () => void | Promise<void>): Promise<void> {
  return Promise.resolve()
    .then(body)
    .then(() => {
      passed += 1;
    })
    .catch((error: unknown) => {
      failures.push(`${name}: ${(error as Error).message}`);
    });
}

function sample(index: number, latencyMs: number, ok = true, status = 200): Sample {
  return { index, dueAt: 0n, latencyMs, status: ok ? status : 0, ok };
}

export async function run(): Promise<number> {
  await check("p95 of 1..100 is 95", () => {
    const values = Array.from({ length: 100 }, (_, index) => index + 1);
    assert.equal(percentile(values, 95), 95);
  });
  await check("nearest-rank is not interpolation", () => {
    const values = Array.from({ length: 100 }, (_, index) => index + 1);
    assert.notEqual(percentile(values, 95), 95.05);
    assert.equal(percentile(values, 50), 50);
    assert.equal(percentile(values, 100), 100);
    assert.equal(percentile(values, 1), 1);
  });
  await check("one sample is every percentile", () => {
    assert.equal(percentile([7], 50), 7);
    assert.equal(percentile([7], 99), 7);
  });
  await check("percentile rejects 0 and 101", () => {
    assert.throws(() => percentile([1], 0), /must be in/);
    assert.throws(() => percentile([1], 101), /must be in/);
  });
  await check("percentile rejects an empty sample", () => {
    assert.throws(() => percentile([], 50), /empty/);
  });
  await check("warm-up samples are dropped and counted", () => {
    const samples = Array.from({ length: 10 }, (_, index) => sample(index, 100 + index));
    const summary = summarize(samples, 3);
    assert.equal(summary.count, 7);
    assert.equal(summary.warmup, 3);
    assert.equal(summary.min, 103);
  });
  await check("summarize does not depend on arrival order", () => {
    const samples = [sample(2, 30), sample(0, 10), sample(1, 20)];
    assert.equal(summarize(samples, 0).p50, 20);
  });
  await check("errorRate counts failures", () => {
    const samples = [sample(0, 1), sample(1, 1, false), sample(2, 1), sample(3, 1), sample(4, 1)];
    const summary = summarize(samples, 0);
    assert.equal(summary.errors, 1);
    assert.equal(summary.errorRate, 0.2);
    assert.equal(summary.statuses.error, 1);
    assert.equal(summary.statuses["200"], 4);
  });
  await check("statuses keep the code, not just ok", () => {
    const summary = summarize([sample(0, 1, false, 503)], 0);
    assert.equal(summary.statuses["503"] ?? summary.statuses.error, 1);
  });
  await check("an all-warm-up run says so", () => {
    assert.throws(() => summarize([sample(0, 1), sample(1, 1)], 2), /no measured samples/);
  });
  await check("threshold parsing", () => {
    const thresholds = parseThresholds(["p95=250", "errorRate=0.01"]);
    assert.deepEqual(thresholds, [
      { name: "p95", limit: 250 },
      { name: "errorRate", limit: 0.01 },
    ]);
  });
  await check("a typo in a threshold name is an error", () => {
    assert.throws(() => parseThresholds(["p9=250"]), /unknown threshold/);
  });
  await check("a non-numeric limit is an error", () => {
    assert.throws(() => parseThresholds(["p95=fast"]), /non-negative number/);
  });
  await check("a bare name is an error", () => {
    assert.throws(() => parseThresholds(["p95"]), /name=value/);
  });
  await check("thresholds mark pass and fail", () => {
    const summary = summarize([sample(0, 10), sample(1, 20), sample(2, 30)], 0);
    const verdicts = evaluate(summary, parseThresholds(["p95=25", "p50=20"]));
    assert.equal(verdicts[0]?.ok, false);
    assert.equal(verdicts[1]?.ok, true);
  });
  await check("render says PASS and FAIL", () => {
    const summary = summarize([sample(0, 10)], 0);
    const passing = build({
      target: "http://127.0.0.1:1/x",
      startedAt: "2026-01-01T00:00:00.000Z",
      requests: 1,
      concurrency: 1,
      warmup: 0,
      wallMs: 1,
      summary,
      thresholds: evaluate(summary, parseThresholds(["p95=100"])),
    });
    assert.match(render(passing), /^result     PASS$/m);
    const failing = build({
      target: "http://127.0.0.1:1/x",
      startedAt: "2026-01-01T00:00:00.000Z",
      requests: 1,
      concurrency: 1,
      warmup: 0,
      wallMs: 1,
      summary,
      thresholds: evaluate(summary, parseThresholds(["p95=1"])),
    });
    assert.match(render(failing), /^result     FAIL \(1 threshold\(s\)\)$/m);
    assert.equal(failing.passed, false);
  });
  await check("throughput divides measured samples by wall clock", () => {
    const summary = summarize([sample(0, 5), sample(1, 5), sample(2, 5), sample(3, 5)], 0);
    const report = build({
      target: "http://127.0.0.1:1/x",
      startedAt: "2026-01-01T00:00:00.000Z",
      requests: 4,
      concurrency: 2,
      warmup: 0,
      wallMs: 1000,
      summary,
      thresholds: [],
    });
    assert.equal(report.requestsPerSecond, 4);
    assert.equal(report.passed, true);
  });
  await check("samplesOf rounds to three decimals", () => {
    assert.deepEqual(samplesOf([sample(0, 1.23456)]), [{ latencyMs: 1.235, ok: true }]);
  });

  const stub = await startStub({ failEvery: 5 });
  const base = `http://127.0.0.1:${stub.port}`;
  try {
    await check("load sends and measures every request", async () => {
      const { samples, wallMs } = await load({ url: `${base}/ok`, requests: 40, concurrency: 4 });
      assert.equal(samples.length, 40);
      assert.equal(samples.filter((entry) => entry.ok).length, 40);
      assert.ok(wallMs > 0);
    });
    await check("indexes are unique, so warm-up means the first N", async () => {
      const { samples } = await load({ url: `${base}/ok`, requests: 20, concurrency: 3 });
      const indexes = samples.map((entry) => entry.index).sort((a, b) => a - b);
      assert.deepEqual(indexes, Array.from({ length: 20 }, (_, index) => index));
    });
    await check("the response body is drained so keep-alive works", async () => {
      const { samples } = await load({ url: `${base}/drip`, requests: 6, concurrency: 2 });
      assert.equal(samples.every((entry) => entry.ok), true);
    });
    await check("a 503 is an error, not a fast success", async () => {
      const { samples } = await load({ url: `${base}/flaky`, requests: 20, concurrency: 1 });
      const summary = summarize(samples, 0);
      assert.ok(summary.errorRate > 0, "expected some failures from /flaky");
      assert.equal(summary.statuses["503"], summary.errors);
    });
    await check("a slow route shows up in the latency", async () => {
      const { samples } = await load({ url: `${base}/slow?ms=25`, requests: 4, concurrency: 2 });
      assert.ok(summarize(samples, 0).p50 >= 20, "expected at least 20 ms");
    });
    await check("a dead port becomes an error sample, not a crash", async () => {
      const { samples } = await load({ url: "http://127.0.0.1:9/ok", requests: 2, concurrency: 1, timeoutMs: 500 });
      assert.equal(samples.length, 2);
      assert.equal(samples.every((entry) => !entry.ok), true);
    });
    await check("concurrency 0 is refused", async () => {
      await assert.rejects(
        load({ url: `${base}/ok`, requests: 1, concurrency: 0 }),
        /concurrency must be at least 1/,
      );
    });
    await check("a bad URL is refused", async () => {
      await assert.rejects(load({ url: "not a url", requests: 1, concurrency: 1 }), /Invalid URL/);
    });
  } finally {
    await stub.close();
  }

  process.stdout.write(`selftest: ${passed} checks passed\n`);
  if (failures.length > 0) {
    for (const failure of failures) process.stderr.write(`selftest: FAILED ${failure}\n`);
    process.stdout.write(`selftest: ${failures.length} of ${passed + failures.length} checks failed\n`);
    return 1;
  }
  return 0;
}
