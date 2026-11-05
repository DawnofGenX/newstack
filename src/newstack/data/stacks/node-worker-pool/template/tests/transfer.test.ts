import assert from "node:assert/strict";
import test from "node:test";

import { Pool } from "../src/pool.js";

test("a transferred buffer is detached on the sender", async () => {
  const pool = new Pool({ size: 1 });
  const buffer = new ArrayBuffer(32 * 1024);
  new Uint8Array(buffer).fill(3);
  const back = await pool.run<{ value: number; buffer: ArrayBuffer }>(
    "checksum",
    { buffer },
    [buffer],
  );
  assert.equal(buffer.byteLength, 0);
  assert.equal(back.buffer.byteLength, 32 * 1024);
  assert.equal(back.value, (32 * 1024 * 3) % 1_000_003);
  await pool.close();
});

test("a checksum without a buffer is refused by the worker", async () => {
  const pool = new Pool({ size: 1 });
  await assert.rejects(pool.run("checksum"), /needs a buffer/);
  await pool.close();
});
