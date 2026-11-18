#!/usr/bin/env node
import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { parseDotEnv, validateEnv } from "./schema.js";

const { values } = parseArgs({
  options: { file: { type: "string" }, allowExtra: { type: "boolean", default: false } },
});

const SCHEMA = {
  NODE_ENV: { type: "enum", values: ["development", "test", "production"], default: "development" },
  PORT: { type: "number", integer: true, min: 1, max: 65535, default: 3000 },
  DEBUG: { type: "boolean", default: false },
  DATABASE_URL: { type: "url", required: true },
  SERVICE_NAME: { type: "string", required: true },
};

try {
  const text = values.file ? readFileSync(values.file, "utf8") : "";
  const env = parseDotEnv(text);
  let { values: resolved, errors } = validateEnv(env, SCHEMA);
  if (values.allowExtra) errors = errors.filter((e) => !/is not in the schema$/.test(e));
  if (errors.length) {
    for (const err of errors) process.stderr.write(`error: ${err}\n`);
    process.exit(1);
  }
  process.stdout.write(JSON.stringify(resolved, null, 2) + "\n");
} catch (err) {
  process.stderr.write(`error: ${err.message}\n`);
  process.exit(1);
}
