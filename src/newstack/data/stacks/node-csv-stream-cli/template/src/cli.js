import { createReadStream, createWriteStream } from "node:fs";
import { parseStream, rowsToObjects, objectsToCsv } from "./csv.js";

function readInput(path) {
  if (!path || path === "-") return process.stdin;
  return createReadStream(path, { encoding: "utf8" });
}

async function csv2json(input, output) {
  const rows = await parseStream(readInput(input));
  const objects = rowsToObjects(rows);
  const json = JSON.stringify(objects, null, 2) + "\n";
  if (!output || output === "-") process.stdout.write(json);
  else {
    const ws = createWriteStream(output);
    ws.write(json);
    ws.end();
  }
}

async function json2csv(input, output) {
  const chunks = [];
  const stream = readInput(input);
  for await (const c of stream) chunks.push(c);
  const objects = JSON.parse(chunks.join(""));
  const csv = objectsToCsv(Array.isArray(objects) ? objects : [objects]);
  if (!output || output === "-") process.stdout.write(csv);
  else {
    const ws = createWriteStream(output);
    ws.write(csv);
    ws.end();
  }
}

const [, , cmd, input, output] = process.argv;
if (cmd === "csv2json") await csv2json(input, output);
else if (cmd === "json2csv") await json2csv(input, output);
else {
  console.error("usage: csv-stream-cli <csv2json|json2csv> <input> [output]");
  process.exit(2);
}