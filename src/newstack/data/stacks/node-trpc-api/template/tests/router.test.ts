import { test } from "node:test";
import assert from "node:assert/strict";
import { appRouter } from "../src/router.js";

test("health via caller", async () => {
  const caller = appRouter.createCaller({});
  assert.deepEqual(await caller.health(), { status: "ok" });
});

test("hello via caller", async () => {
  const caller = appRouter.createCaller({});
  assert.equal(await caller.hello({ name: "world" }), "Hello world");
});

test("add mutation via caller", async () => {
  const caller = appRouter.createCaller({});
  assert.equal(await caller.add({ a: 2, b: 3 }), 5);
});