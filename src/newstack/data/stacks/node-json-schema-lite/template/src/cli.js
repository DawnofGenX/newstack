#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { validate } from "./schema.js";

const PROGRAM = "{{ npm_name }}";
const USAGE = `usage: ${PROGRAM} --schema FILE [--data FILE]

Validates a JSON document against a JSON Schema subset. With no --data it reads
the document from stdin. Prints "valid", or one "path: message" line per
problem and exits 1.`;

function readJson(source, what) {
  const text = source === "-"
    ? readFileSync(0, "utf8")
    : readFileSync(source, "utf8");
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`${what} is not valid JSON: ${error.message}`);
  }
}

export function main(argv, io = {}) {
  const out = io.out ?? ((line) => console.log(line));
  const err = io.err ?? ((line) => console.error(line));
  let schemaPath = null;
  let dataPath = null;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "-h" || arg === "--help") {
      out(USAGE);
      return 0;
    }
    if (arg === "--schema" || arg === "--data") {
      const value = argv[index + 1];
      if (value === undefined) {
        err(`${arg} needs a file`);
        return 2;
      }
      if (arg === "--schema") schemaPath = value;
      else dataPath = value;
      index += 1;
    } else {
      err(`unknown argument: ${arg}`);
      err(USAGE);
      return 2;
    }
  }
  if (schemaPath === null) {
    err("--schema is required");
    err(USAGE);
    return 2;
  }
  let schema;
  let document;
  try {
    schema = readJson(schemaPath, "schema");
    document = readJson(dataPath ?? "-", "document");
  } catch (error) {
    err(error.message);
    return 1;
  }
  const problems = validate(document, schema);
  if (problems.length === 0) {
    out("valid");
    return 0;
  }
  for (const problem of problems) err(`${problem.path}: ${problem.message}`);
  return 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}
