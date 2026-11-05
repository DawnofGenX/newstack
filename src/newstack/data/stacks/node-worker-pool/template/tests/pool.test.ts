import assert from "node:assert/strict";
import test from "node:test";

import { Pool, PoolError } from "../src/pool.js";

test("a pool runs many tasks on few workers", async () => {
  const pool = new Pool({ size: 2 });
  const sums = await Promise.all(
    Array.from({ length: 12 }, (_, index) => pool.run<number>("sum", { values: [index, 1] })),
  );
  const stats = pool.stats();
  assert.equal(sums.length, 12);
  assert.equal(sums[11], 12);
  assert.ok(stats.spawns <= 2, `spawned ${stats.spawns}`);
  assert.equal(stats.completed, 12);
  assert.equal(stats.failed, 0);
  assert.equal(await pool.close().then((report) => report.completed), 12);
});

test("warm spawns the pool before any task arrives", async () => {
  const pool = new Pool({ size: 3 });
  await pool.warm();
  assert.equal(pool.stats().spawns, 3);
  assert.equal(pool.stats().idle, 3);
  await pool.close();
});

test("a full queue refuses rather than growing", async () => {
  const pool = new Pool({ size: 1, maxQueue: 1 });
  const outcomes = await Promise.all(
    Array.from({ length: 4 }, () =>
      pool.run("spin", { ms: 40 }).then(
        () => "ran",
        (error: Error) => error.message,
      ),
    ),
  );
  assert.ok(outcomes.includes("ran"));
  const refusals = outcomes.filter((outcome) => outcome.includes("maxQueue limit"));
  assert.ok(refusals.length >= 1, outcomes.join(" | "));
  const report = await pool.close();
  assert.ok(report.refused >= 1);
});

test("a closed pool accepts no new work", async () => {
  const pool = new Pool({ size: 1 });
  await pool.run("sum", { values: [1] });
  await pool.close();
  await assert.rejects(pool.run("sum", { values: [1] }), /closing/);
});

test("construction refuses impossible sizes", () => {
  assert.throws(() => new Pool({ size: 0 }), PoolError);
  assert.throws(() => new Pool({ size: 1.5 }), PoolError);
  assert.throws(() => new Pool({ maxQueue: -1 }), PoolError);
});

test("close waits for the backlog it accepted", async () => {
  const pool = new Pool({ size: 1, maxQueue: 8 });
  const jobs = Array.from({ length: 5 }, () => pool.run("spin", { ms: 10 }));
  const values = await Promise.all(jobs);
  const report = await pool.close();
  assert.equal(values.length, 5);
  assert.equal(report.completed, 5);
  assert.equal(report.refused, 0);
});
