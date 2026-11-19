import { pathToFileURL } from "node:url";
import { readFileSync, existsSync } from "node:fs";
import { formatSql } from "./format.js";

export function main(argv) {
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") { process.stdout.write("usage: sqlfmt [sql-or-file]\n"); return 0; }
    else if (a === "-") positional.push("-");
    else if (a.startsWith("-")) { process.stderr.write(`unknown flag ${a}\n`); return 2; }
    else positional.push(a);
  }
  if (positional.length === 0) {
    process.stdout.write(formatSql(readFileSync(0, "utf8")) + "\n");
    return 0;
  }
  const allFiles = positional.every((p) => p === "-" || existsSync(p));
  if (allFiles) {
    for (const f of positional) {
      const s = f === "-" ? readFileSync(0, "utf8") : readFileSync(f, "utf8");
      process.stdout.write(formatSql(s) + "\n");
    }
    return 0;
  }
  process.stdout.write(formatSql(positional.join(" ")) + "\n");
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}