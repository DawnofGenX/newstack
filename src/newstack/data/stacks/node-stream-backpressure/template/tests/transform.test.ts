import assert from "node:assert/strict";
import test from "node:test";

import { ForgettingTransform, TwiceTransform, drive } from "../src/transform.js";

test("a transform that never calls its callback stalls without an error", async () => {
  const report = await drive(new ForgettingTransform(), [1, 2, 3], 120);
  assert.equal(report.settled, false);
  assert.equal(report.error, null);
  assert.ok(report.output >= 1, "it pushed nothing at all");
});

test("a transform that calls its callback twice fails the stream", async () => {
  const report = await drive(new TwiceTransform(), [1], 120);
  assert.match(report.error ?? "", /multiple times/);
  assert.equal(report.settled, false);
});

test("drive reports what it waited for", async () => {
  const report = await drive(new ForgettingTransform(), [], 40);
  assert.equal(report.waitedMs, 40);
});

test("a healthy stream settles before the timeout", async () => {
  const { PassThrough } = await import("node:stream");
  const report = await drive(new PassThrough({ objectMode: true }), [1, 2], 40);
  assert.equal(report.settled, true);
  assert.equal(report.error, null);
});
