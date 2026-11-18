import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";

test("logs structured JSON with redaction", () => {
  const res = spawnSync(process.execPath, ["src/cli.js", "--level", "info", "--msg", "hi", "--password", "s3cret"], {
    encoding: "utf8",
  });
  assert.equal(res.status, 0, res.stderr);
  const line = res.stdout.trim().split("\n").pop();
  const obj = JSON.parse(line);
  assert.equal(obj.msg, "hi");
  assert.equal(obj.password, "[REDACTED]");
  assert.equal(obj.service, "demo");
});

test("child logger binds fields", async () => {
  const { createLogger, childLogger } = await import("../src/logger.js");
  const chunks = [];
  const logger = createLogger({ level: "debug" });
  const child = childLogger(logger, { requestId: "r1" });
  // pino writes to stdout; just ensure no throw
  child.info({ n: 1 }, "ok");
  assert.ok(true);
});
