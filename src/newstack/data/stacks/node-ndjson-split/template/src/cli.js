#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { parseArgs } from "node:util";
import { parseNdjson, splitRecords, serialize, partName } from "./split.js";

const { values } = parseArgs({
  options: {
    file: { type: "string" },
    "out-dir": { type: "string" },
    "max-lines": { type: "string" },
    "max-bytes": { type: "string" },
  },
});

const outDir = values["out-dir"];
const maxLines = values["max-lines"];
const maxBytes = values["max-bytes"];

if (!values.file || !outDir) {
  process.stderr.write("usage: cli.js --file data.ndjson --out-dir out [--max-lines N] [--max-bytes N]\n");
  process.exit(2);
}

try {
  const records = parseNdjson(readFileSync(values.file, "utf8"));
  const chunks = splitRecords(records, {
    maxLines: maxLines !== undefined ? Number(maxLines) : undefined,
    maxBytes: maxBytes !== undefined ? Number(maxBytes) : undefined,
  });
  mkdirSync(outDir, { recursive: true });
  const parts = chunks.map((chunk, i) => {
    const name = partName(i + 1);
    writeFileSync(join(outDir, name), serialize(chunk));
    return { part: name, records: chunk.length };
  });
  process.stdout.write(JSON.stringify({ records: records.length, chunks: chunks.length, parts }, null, 2) + "\n");
} catch (err) {
  process.stderr.write(`error: ${err.message}\n`);
  process.exit(1);
}
