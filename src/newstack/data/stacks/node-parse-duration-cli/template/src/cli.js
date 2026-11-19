import { pathToFileURL } from "node:url";
import { parseDuration } from "./parse.js";

export function main(argv) {
  if (argv.includes("--help") || argv.includes("-h")) {
    process.stdout.write("usage: parse-duration <duration>\n");
    return 0;
  }
  const input = argv.join(" ");
  if (!input) { process.stderr.write("missing duration\n"); return 2; }
  try {
    process.stdout.write(String(parseDuration(input)) + "\n");
    return 0;
  } catch (e) {
    process.stderr.write(e.message + "\n");
    return 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}