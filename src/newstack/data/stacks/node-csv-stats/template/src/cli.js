#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { parseCsv, summarize } from "./csv.js";

const { values } = parseArgs({ options: { file: { type: "string" }, table: { type: "boolean", default: false } } });

if (!values.file) {
  process.stderr.write("usage: cli.js --file data.csv [--table]\n");
  process.exit(2);
}

try {
  const { headers, rows } = parseCsv(readFileSync(values.file, "utf8"));
  const stats = summarize(headers, rows);
  if (values.table) {
    const width = Math.max(6, ...headers.map((h) => h.length));
    process.stdout.write(`${"column".padEnd(width)}  rows  empty  distinct  numeric\n`);
    for (const s of stats) {
      const numeric = s.numeric ? `mean ${s.numeric.mean}` : "-";
      process.stdout.write(`${s.column.padEnd(width)}  ${String(s.rows).padStart(4)}  ${String(s.empty).padStart(5)}  ${String(s.distinct).padStart(8)}  ${numeric}\n`);
    }
  } else {
    process.stdout.write(JSON.stringify({ rows: rows.length, columns: stats }, null, 2) + "\n");
  }
} catch (err) {
  process.stderr.write(`error: ${err.message}\n`);
  process.exit(1);
}
