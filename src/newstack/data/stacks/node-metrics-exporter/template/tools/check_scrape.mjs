// tools/check_scrape.mjs — validate a scrape the way a Prometheus server would.
// Reads the exposition text on stdin so it can be used as
//   curl -sS http://127.0.0.1:5474/metrics | node tools/check_scrape.mjs
// Any format violation (missing HELP, non-monotonic bucket, duplicate series) is a
// hard failure with the line number, not a silent partial import.

import { parseExposition } from "../src/exposition.js";

let raw = "";
for await (const chunk of process.stdin) raw += chunk;

try {
  const families = parseExposition(raw);
  const names = [...families.keys()].sort();
  console.log(`scrape ok: ${names.length} families, ${raw.split("\n").length - 1} lines`);
  console.log(names.join("\n"));
} catch (error) {
  console.error(`scrape invalid: ${error.message}`);
  process.exit(1);
}
