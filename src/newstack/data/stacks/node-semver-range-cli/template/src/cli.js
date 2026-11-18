#!/usr/bin/env node
import { parseArgs } from "node:util";
import { parse, compare, satisfies } from "./semver.js";

const { values, positionals } = parseArgs({
  options: {},
  allowPositionals: true,
});

const [version, range] = positionals;
if (!version || !range) {
  if (positionals[0] === "--help" || positionals[0] === "-h") {
    process.stdout.write("Usage: semver-range <version> <range>\n");
    process.exit(0);
  }
  console.error("Usage: semver-range <version> <range>");
  process.exit(2);
}

const ok = satisfies(version, range);
const match = String(range).match(/\d+\.\d+\.\d+/);
let cmp = 0;
if (match) {
  try {
    cmp = compare(version, match[0]);
  } catch {
    cmp = 0;
  }
}
process.stdout.write((ok ? "satisfied" : "not satisfied") + "\n");
process.stdout.write(`comparison: ${cmp}\n`);
process.exit(ok ? 0 : 1);
