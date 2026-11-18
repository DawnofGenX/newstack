#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { applyPatch, diff } from "./patch.js";

const args = process.argv.slice(2);
const cmd = args[0];

function readJson(p) {
  return JSON.parse(readFileSync(p, "utf8"));
}

if (cmd === "apply") {
  const docPath = args[1];
  const patchPath = args[2];
  const doc = readJson(docPath);
  const patch = readJson(patchPath);
  const out = applyPatch(doc, patch);
  process.stdout.write(JSON.stringify(out, null, 2) + "\n");
} else if (cmd === "diff") {
  const a = readJson(args[1]);
  const b = readJson(args[2]);
  const ops = diff(a, b);
  process.stdout.write(JSON.stringify(ops, null, 2) + "\n");
} else {
  console.error("usage: json-patch-cli apply <doc.json> <patch.json>");
  console.error("       json-patch-cli diff <a.json> <b.json>");
  process.exit(2);
}