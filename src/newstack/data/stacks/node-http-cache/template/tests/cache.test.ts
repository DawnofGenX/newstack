import assert from "node:assert/strict";
import { test } from "node:test";
import { HttpCache, maxAgeMs } from "../src/cache.js";
import { library } from "../src/demo.js";
import { createServer } from "../src/server.js";

test("max-age is read in seconds and no-store is zero", () => {
  assert.equal(maxAgeMs("max-age=1"), 1_000);
  assert.equal(maxAgeMs("public, max-age=60"), 60_000);
  assert.equal(maxAgeMs("no-store"), 0);
  assert.equal(maxAgeMs(undefined), 0);
});

test("a fresh entry is served without a request", async () => {
  const handle = await createServer(library());
  try {
    const cache = new HttpCache(`http://127.0.0.1:${handle.port}`, { clock: () => 0 });
    const first = await cache.get("/ticker");
    const second = await cache.get("/ticker");
    assert.ok(first.bytes > 0);
    assert.equal(second.fromCache, true);
    assert.equal(second.bytes, 0);
    assert.equal(second.body, first.body);
    assert.equal(cache.entry("/ticker", "application/json")?.hits, 1);
  } finally {
    await handle.close();
  }
});

test("an expired entry revalidates and keeps its body", async () => {
  const handle = await createServer(library());
  try {
    let now = 0;
    const cache = new HttpCache(`http://127.0.0.1:${handle.port}`, { clock: () => now });
    const first = await cache.get("/ticker");
    now = 1_500;
    const again = await cache.get("/ticker");
    assert.equal(again.revalidated, true);
    assert.equal(again.body, first.body);
    assert.equal(cache.entry("/ticker", "application/json")?.revalidations, 1);
  } finally {
    await handle.close();
  }
});

test("copying the 304 body empties the entry", async () => {
  const handle = await createServer(library());
  try {
    let now = 0;
    const cache = new HttpCache(`http://127.0.0.1:${handle.port}`, {
      clock: () => now,
      dropBodyOn304: true,
    });
    await cache.get("/ticker");
    now = 1_500;
    const lost = await cache.get("/ticker");
    assert.equal(lost.bodyLost, true);
    const empty = await cache.get("/ticker");
    assert.equal(empty.fromCache, true);
    assert.equal(empty.body, "");
  } finally {
    await handle.close();
  }
});

test("a url key cannot tell two representations apart", async () => {
  const handle = await createServer(library());
  try {
    const origin = `http://127.0.0.1:${handle.port}`;
    const urlKeyed = new HttpCache(origin, { clock: () => 0, keyMode: "url" });
    const json = await urlKeyed.get("/report", "application/json");
    const text = await urlKeyed.get("/report", "text/plain");
    assert.equal(text.body, json.body);
    const varyKeyed = new HttpCache(origin, { clock: () => 0, keyMode: "vary" });
    const json2 = await varyKeyed.get("/report", "application/json");
    const text2 = await varyKeyed.get("/report", "text/plain");
    assert.notEqual(text2.body, json2.body);
  } finally {
    await handle.close();
  }
});

test("no-store is never stored", async () => {
  const handle = await createServer(library());
  try {
    const cache = new HttpCache(`http://127.0.0.1:${handle.port}`, { clock: () => 0 });
    await cache.get("/private");
    assert.equal(cache.entry("/private", "application/json"), undefined);
  } finally {
    await handle.close();
  }
});
