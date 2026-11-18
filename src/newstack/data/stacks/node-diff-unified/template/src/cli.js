#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { unifiedDiff } from "./diff.js";

const [oldPath, newPath] = process.argv.slice(2);
if (!oldPath || !newPath) {
  console.error("usage: node src/cli.js OLD NEW");
  process.exit(2);
}
const diff = unifiedDiff(readFileSync(oldPath, "utf8"), readFileSync(newPath, "utf8"), {
  oldLabel: oldPath,
  newLabel: newPath,
});
if (diff === "") {
  console.log("identical");
} else {
  process.stdout.write(diff);
}
