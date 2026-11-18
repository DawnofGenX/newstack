import { test } from "node:test";
import assert from "node:assert/strict";
import { app } from "../src/app.js";
import * as store from "../src/store.js";

test("health", async () => {
  const res = await app.request("/health");
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { ok: true });
});

test("crud lifecycle", async () => {
  store.reset();
  let res = await app.request("/items", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name: "apple", price: 1.5 }),
  });
  assert.equal(res.status, 201);
  const created = await res.json();
  assert.equal(created.name, "apple");

  res = await app.request("/items");
  assert.equal((await res.json()).length, 1);

  res = await app.request(`/items/${created.id}`);
  assert.equal((await res.json()).name, "apple");

  res = await app.request(`/items/${created.id}`, {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ price: 2 }),
  });
  assert.equal((await res.json()).price, 2);

  res = await app.request(`/items/${created.id}`, { method: "DELETE" });
  assert.equal(res.status, 204);

  res = await app.request(`/items/${created.id}`);
  assert.equal(res.status, 404);
});

test("post requires name", async () => {
  store.reset();
  const res = await app.request("/items", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({}),
  });
  assert.equal(res.status, 400);
});