import { pathToFileURL } from "node:url";
import { readFileSync } from "node:fs";
import { crc32c } from "./crc.js";

export function main(argv) {
  const files = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") {
      process.stdout.write("usage: crc32c [file|-]\n");
      return 0;
    } else if (a === "-") files.push("-");
    else if (a.startsWith("-")) { process.stderr.write(`unknown flag ${a}\n`); return 2; }
    else files.push(a);
  }
  if (files.length === 0) files.push("-");
  for (const f of files) {
    const s = f === "-" ? readFileSync(0, "utf8") : readFileSync(f, "utf8");
    const val = crc32c(s);
    process.stdout.write("0x" + val.toString(16).toUpperCase().padStart(8, "0") + "\n");
  }
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}