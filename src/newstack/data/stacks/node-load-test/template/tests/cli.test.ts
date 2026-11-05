import assert from "node:assert/strict";
import test from "node:test";
import { main } from "../src/main.js";
import { startStub } from "../src/stub.js";

test("help and version are free", async () => {
  assert.equal(await main(["help"]), 0);
  assert.equal(await main(["--version"]), 0);
  assert.equal(await main([]), 0);
});

test("a run with no target is unusable, not a pass", async () => {
  assert.equal(await main(["run"]), 2);
  assert.equal(await main(["run", "--target", "not a url"]), 2);
  assert.equal(await main(["run", "--target", "http://127.0.0.1:9/", "--warmup", "5", "--requests", "5"]), 2);
  assert.equal(await main(["fly"]), 2);
  assert.equal(await main(["run", "--target", "http://127.0.0.1:9/", "--threshold", "p9=1"]), 2);
});

test("a passing threshold exits 0 and a failing one exits 1", async () => {
  const stub = await startStub();
  const target = `http://127.0.0.1:${stub.port}/ok`;
  try {
    assert.equal(
      await main(["run", "--target", target, "--requests", "20", "--warmup", "2", "--threshold", "p95=2000"]),
      0,
    );
    assert.equal(
      await main(["run", "--target", target, "--requests", "20", "--warmup", "2", "--threshold", "p95=0"]),
      1,
    );
  } finally {
    await stub.close();
  }
});

test("errors fail the default error-rate gate", async () => {
  const stub = await startStub({ failEvery: 2 });
  try {
    const code = await main([
      "run",
      "--target",
      `http://127.0.0.1:${stub.port}/flaky`,
      "--requests",
      "10",
      "--warmup",
      "0",
    ]);
    assert.equal(code, 1);
  } finally {
    await stub.close();
  }
});
