import test from "node:test";
import assert from "node:assert/strict";
import { createCache } from "../src/cache.js";

test("a stored value comes back and counts as a hit", () => {
  const cache = createCache();
  cache.set("a", 1);
  assert.equal(cache.get("a"), 1);
  assert.deepEqual(cache.stats().hits, 1);
});

test("a missing key is a miss", () => {
  const cache = createCache();
  assert.equal(cache.get("nope"), undefined);
  assert.equal(cache.stats().misses, 1);
});

test("the least recently used key is evicted when the cache is full", () => {
  const cache = createCache({ capacity: 2 });
  cache.set("a", 1);
  cache.set("b", 2);
  assert.equal(cache.get("a"), 1);
  cache.set("c", 3);
  assert.deepEqual(cache.keys(), ["a", "c"]);
  assert.equal(cache.get("b"), undefined);
  assert.equal(cache.stats().evictions, 1);
});

test("rewriting a key does not evict another one", () => {
  const cache = createCache({ capacity: 2 });
  cache.set("a", 1);
  cache.set("b", 2);
  cache.set("a", 3);
  assert.deepEqual(cache.keys(), ["b", "a"]);
  assert.equal(cache.get("a"), 3);
  assert.equal(cache.stats().evictions, 0);
});

test("an entry expires once the clock reaches its deadline", () => {
  let clock = 1000;
  const cache = createCache({ ttlMs: 500, now: () => clock });
  cache.set("a", 1);
  clock = 1499;
  assert.equal(cache.get("a"), 1);
  clock = 1500;
  assert.equal(cache.get("a"), undefined);
  assert.equal(cache.stats().expirations, 1);
});

test("a per-entry ttl overrides the default", () => {
  let clock = 0;
  const cache = createCache({ ttlMs: 10_000, now: () => clock });
  cache.set("short", 1, { ttlMs: 10 });
  cache.set("long", 2);
  clock = 11;
  assert.equal(cache.get("short"), undefined);
  assert.equal(cache.get("long"), 2);
});

test("a zero ttl means the entry never expires", () => {
  let clock = 0;
  const cache = createCache({ now: () => clock });
  cache.set("a", 1);
  clock = 10 ** 9;
  assert.equal(cache.get("a"), 1);
});

test("sweep drops expired entries without reading them", () => {
  let clock = 0;
  const cache = createCache({ ttlMs: 5, now: () => clock });
  cache.set("a", 1);
  cache.set("b", 2);
  clock = 5;
  assert.equal(cache.sweep(), 2);
  assert.equal(cache.size, 0);
});

test("the hit rate is zero before any lookup", () => {
  assert.equal(createCache().stats().hitRate, 0);
});

test("an invalid capacity is refused", () => {
  assert.throws(() => createCache({ capacity: 0 }), RangeError);
});

test("the hit rate reflects hits over lookups", () => {
  const cache = createCache();
  cache.set("a", 1);
  cache.get("a");
  cache.get("b");
  assert.equal(cache.stats().hitRate, 0.5);
});
