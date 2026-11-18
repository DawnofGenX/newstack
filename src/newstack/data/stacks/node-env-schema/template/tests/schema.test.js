import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { parseDotEnv, validateEnv, coerce } from "../src/schema.js";

const SCHEMA = {
  PORT: { type: "number", integer: true, min: 1, max: 65535 },
  DEBUG: { type: "boolean", default: false },
  DATABASE_URL: { type: "url", required: true },
  MODE: { type: "enum", values: ["dev", "prod"], default: "dev" },
};

test("parses key=value, quotes, export and comments", () => {
  const env = parseDotEnv(`
# a comment
export PORT=8080
DATABASE_URL="https://db.example.com/x"
MODE='prod'   # trailing
`);
  assert.deepEqual(env, { PORT: "8080", DATABASE_URL: "https://db.example.com/x", MODE: "prod" });
});

test("rejects malformed lines, bad keys and duplicates", () => {
  assert.throws(() => parseDotEnv("NOPE"), /malformed line/);
  assert.throws(() => parseDotEnv("1BAD=1"), /invalid key/);
  assert.throws(() => parseDotEnv("A=1\nA=2"), /duplicate key/);
});

test("coerces numbers with bounds and integers", () => {
  assert.equal(coerce("PORT", "8080", SCHEMA.PORT), 8080);
  assert.throws(() => coerce("PORT", "0", SCHEMA.PORT), /must be >= 1/);
  assert.throws(() => coerce("PORT", "1.5", SCHEMA.PORT), /must be an integer/);
  assert.throws(() => coerce("PORT", "abc", SCHEMA.PORT), /must be a number/);
});

test("coerces booleans leniently", () => {
  for (const v of ["1", "true", "YES", "on"]) assert.equal(coerce("DEBUG", v, SCHEMA.DEBUG), true);
  for (const v of ["0", "false", "no", "off"]) assert.equal(coerce("DEBUG", v, SCHEMA.DEBUG), false);
  assert.throws(() => coerce("DEBUG", "maybe", SCHEMA.DEBUG), /must be a boolean/);
});

test("validates urls and enums", () => {
  assert.equal(coerce("DATABASE_URL", "https://db.example.com", SCHEMA.DATABASE_URL), "https://db.example.com/");
  assert.throws(() => coerce("DATABASE_URL", "ftp://nope", SCHEMA.DATABASE_URL), /must be an http\(s\) url/);
  assert.throws(() => coerce("MODE", "staging", SCHEMA.MODE), /must be one of dev, prod/);
});

test("applies defaults and reports missing required keys", () => {
  const { values, errors } = validateEnv({ PORT: "9000" }, SCHEMA);
  assert.deepEqual(values, { PORT: 9000, DEBUG: false, MODE: "dev" });
  assert.deepEqual(errors, ["DATABASE_URL is required"]);
});

test("reports keys outside the schema", () => {
  const { errors } = validateEnv({ DATABASE_URL: "https://x.example.com", EXTRA: "1" }, SCHEMA);
  assert.ok(errors.includes("EXTRA is not in the schema"), errors.join("; "));
});

test("cli prints typed json and fails on invalid env", () => {
  const dir = mkdtempSync(join(tmpdir(), "env-"));
  const good = join(dir, "good.env");
  writeFileSync(good, "SERVICE_NAME=api\nDATABASE_URL=https://db.example.com\nPORT=8080\n");
  const ok = spawnSync(process.execPath, ["src/cli.js", "--file", good], { encoding: "utf8" });
  assert.equal(ok.status, 0, ok.stderr);
  const parsed = JSON.parse(ok.stdout);
  assert.deepEqual(parsed, { NODE_ENV: "development", PORT: 8080, DEBUG: false, DATABASE_URL: "https://db.example.com/", SERVICE_NAME: "api" });

  const bad = join(dir, "bad.env");
  writeFileSync(bad, "SERVICE_NAME=api\nDATABASE_URL=https://db.example.com\nPORT=99999\n");
  const fail = spawnSync(process.execPath, ["src/cli.js", "--file", bad], { encoding: "utf8" });
  assert.equal(fail.status, 1);
  assert.match(fail.stderr, /PORT must be <= 65535/);
});
