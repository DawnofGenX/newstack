import { pathToFileURL } from "node:url";
import { readFileSync } from "node:fs";
import { encodeEntities, decodeEntities } from "./html.js";

export function main(argv) {
  let mode = "encode";
  const files = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--decode" || a === "-d") mode = "decode";
    else if (a === "--encode" || a === "-e") mode = "encode";
    else if (a === "--help" || a === "-h") {
      process.stdout.write("usage: html-entities [--encode|--decode] [file|-]\n");
      return 0;
    } else if (a === "-") files.push("-");
    else if (a.startsWith("-")) {
      process.stderr.write(`unknown flag ${a}\n`);
      return 2;
    } else files.push(a);
  }
  const transform = mode === "decode" ? decodeEntities : encodeEntities;
  if (files.length === 0) files.push("-");
  for (const f of files) {
    const s = f === "-" ? readFileSync(0, "utf8") : readFileSync(f, "utf8");
    process.stdout.write(transform(s));
  }
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}