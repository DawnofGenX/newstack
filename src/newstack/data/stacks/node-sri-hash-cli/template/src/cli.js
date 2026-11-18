#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { sriFor, verify, verifyManifest, readManifest } from "./sri.js";

const [, , command, ...args] = process.argv;

function fail(message) {
  process.stderr.write(`error: ${message}\n`);
  process.exit(2);
}

try {
  if (command === "hash") {
    if (args.length === 0) fail("hash needs at least one file");
    const algorithm = args[0].startsWith("--algo=") ? args.shift().slice(7) : "sha384";
    for (const file of args) {
      process.stdout.write(`${sriFor(readFileSync(file), algorithm)}  ${file}\n`);
    }
  } else if (command === "verify") {
    const [file, integrity] = args;
    if (!file || !integrity) fail("verify needs <file> <integrity>");
    const ok = verify(readFileSync(file), integrity);
    process.stdout.write(ok ? "ok\n" : "fail\n");
    if (!ok) process.exit(1);
  } else if (command === "manifest") {
    const [path] = args;
    if (!path) fail("manifest needs <manifest.json>");
    const { dir, manifest } = readManifest(path);
    const results = verifyManifest(dir, manifest);
    process.stdout.write(JSON.stringify(results, null, 2) + "\n");
    if (results.some((r) => !r.ok)) process.exit(1);
  } else {
    fail("usage: cli.js <hash|verify|manifest> ...");
  }
} catch (err) {
  fail(err.message);
}
