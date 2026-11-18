import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import {
  DEFAULTS,
  loadConfig,
  configFromEnv,
  readFileConfig,
} from "../src/config.js";

test("defaults", () => {
  const cfg = loadConfig({});
  assert.deepEqual(cfg, DEFAULTS);
});

test("precedence file < env < cli", () => {
  const cfg = loadConfig({
    defaults: DEFAULTS,
    fileConfig: { port: 4000, host: "filehost" },
    envConfig: { port: 5000 },
    cliConfig: { port: 6000 },
  });
  assert.equal(cfg.port, 6000);
  assert.equal(cfg.host, "filehost");
});

test("env overrides file", () => {
  const cfg = loadConfig({
    fileConfig: { port: 4000 },
    envConfig: { port: 5000 },
  });
  assert.equal(cfg.port, 5000);
});

test("configFromEnv", () => {
  const env = { APP_PORT: "7000", APP_DEBUG: "true", APP_NAME: "x" };
  assert.deepEqual(configFromEnv(env), { port: 7000, debug: true, name: "x" });
});

test("readFileConfig", () => {
  const dir = mkdtempSync(join(tmpdir(), "cfg-"));
  const p = join(dir, "c.json");
  writeFileSync(p, JSON.stringify({ port: 9000 }));
  assert.deepEqual(readFileConfig(p), { port: 9000 });
});

test("cli writes resolved json", () => {
  const dir = mkdtempSync(join(tmpdir(), "cfg-"));
  const cfgPath = join(dir, "c.json");
  const outPath = join(dir, "out.json");
  writeFileSync(cfgPath, JSON.stringify({ port: 4000, host: "filehost" }));
  const res = spawnSync(
    process.execPath,
    ["src/cli.js", "--config", cfgPath, "--port", "6000", "--out", outPath],
    { env: { ...process.env, APP_PORT: "5000" }, encoding: "utf8" }
  );
  assert.equal(res.status, 0, res.stderr);
  const out = JSON.parse(readFileSync(outPath, "utf8"));
  assert.equal(out.port, 6000);
  assert.equal(out.host, "filehost");
});