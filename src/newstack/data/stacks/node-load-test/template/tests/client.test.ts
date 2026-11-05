import assert from "node:assert/strict";
import test from "node:test";
import { load } from "../src/client.js";
import { startStub } from "../src/stub.js";
import { summarize } from "../src/stats.js";

test("load sends exactly the requested number of requests", async () => {
  const stub = await startStub();
  try {
    const { samples, wallMs } = await load({
      url: `http://127.0.0.1:${stub.port}/ok`,
      requests: 40,
      concurrency: 4,
    });
    assert.equal(samples.length, 40);
    assert.equal(samples.every((sample) => sample.ok), true);
    assert.ok(wallMs > 0);
    const indexes = samples.map((sample) => sample.index).sort((a, b) => a - b);
    assert.deepEqual(indexes, Array.from({ length: 40 }, (_, index) => index));
  } finally {
    await stub.close();
  }
});

test("a 503 counts as an error", async () => {
  const stub = await startStub({ failEvery: 4 });
  try {
    const { samples } = await load({
      url: `http://127.0.0.1:${stub.port}/flaky`,
      requests: 12,
      concurrency: 1,
    });
    const summary = summarize(samples, 0);
    assert.equal(summary.errors, 3);
    assert.equal(summary.statuses["503"], 3);
  } finally {
    await stub.close();
  }
});

test("the body is drained, so a chunked response still finishes", async () => {
  const stub = await startStub();
  try {
    const { samples } = await load({
      url: `http://127.0.0.1:${stub.port}/drip`,
      requests: 6,
      concurrency: 2,
    });
    assert.equal(samples.every((sample) => sample.ok), true);
  } finally {
    await stub.close();
  }
});

test("a refused connection becomes an error sample", async () => {
  const { samples } = await load({
    url: "http://127.0.0.1:9/ok",
    requests: 2,
    concurrency: 1,
    timeoutMs: 500,
  });
  assert.equal(samples.length, 2);
  assert.equal(samples.every((sample) => !sample.ok), true);
  assert.ok((samples[0]?.error ?? "").length > 0);
});

test("nonsense options are refused before anything is sent", async () => {
  await assert.rejects(load({ url: "http://127.0.0.1:9/", requests: 0, concurrency: 1 }), /requests/);
  await assert.rejects(
    load({ url: "http://127.0.0.1:9/", requests: 1, concurrency: 0 }),
    /concurrency/,
  );
  await assert.rejects(load({ url: "nope", requests: 1, concurrency: 1 }), /Invalid URL/);
});
