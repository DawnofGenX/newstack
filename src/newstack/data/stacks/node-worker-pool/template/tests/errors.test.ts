import assert from "node:assert/strict";
import test from "node:test";

import { Pool } from "../src/pool.js";

test("a throwing task carries the worker's message", async () => {
  const pool = new Pool({ size: 1 });
  await assert.rejects(pool.run("boom"), /the task failed on purpose/);
  await pool.close();
});

test("a worker that exits rejects its task instead of hanging", async () => {
  const pool = new Pool({ size: 1 });
  await assert.rejects(pool.run("exit"), /exited with code 7/);
  await pool.close();
});

test("the pool replaces a dead worker and keeps serving", async () => {
  const pool = new Pool({ size: 1 });
  await assert.rejects(pool.run("exit"), /exited with code 7/);
  assert.equal(await pool.run<number>("sum", { values: [5, 6] }), 11);
  const stats = pool.stats();
  assert.ok(stats.replaced >= 1, `replaced ${stats.replaced}`);
  assert.ok(stats.spawns >= 2, `spawns ${stats.spawns}`);
  const report = await pool.close();
  assert.equal(report.failed, 1);
});
