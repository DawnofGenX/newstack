import { test } from "node:test";
import assert from "node:assert/strict";
import { createLimiter } from "../src/limiter.js";

test("allows N then rejects", () => {
  let now = 0;
  const limiter = createLimiter({ limit: 3, windowMs: 1000, now: () => now });
  assert.equal(limiter.tryAcquire().allowed, true);
  assert.equal(limiter.tryAcquire().allowed, true);
  assert.equal(limiter.tryAcquire().allowed, true);
  const r = limiter.tryAcquire();
  assert.equal(r.allowed, false);
  assert.ok(r.retryAfter >= 1);
});

test("resets after window", () => {
  let now = 0;
  const limiter = createLimiter({ limit: 1, windowMs: 1000, now: () => now });
  assert.equal(limiter.tryAcquire().allowed, true);
  assert.equal(limiter.tryAcquire().allowed, false);
  now = 1000;
  assert.equal(limiter.tryAcquire().allowed, true);
});

test("stats", () => {
  let now = 0;
  const limiter = createLimiter({ limit: 2, windowMs: 1000, now: () => now });
  limiter.tryAcquire();
  const s = limiter.stats();
  assert.equal(s.count, 1);
  assert.equal(s.remaining, 1);
});
