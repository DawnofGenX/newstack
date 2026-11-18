#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { parseYaml, stringifyYaml, getPath, YamlError } from "./yaml.js";

const USAGE = `usage: {{ npm_name }} [--json | --get PATH | --yaml] [FILE]

Reads YAML from FILE or standard input.

  --json        print JSON instead of YAML
  --get PATH    print one value, e.g. server.hosts[0]
  --yaml        read JSON and print YAML
  -h, --help    print this message

Exit status is 1 for a parse error or a missing path and 2 for bad usage.`;

export function main(argv, io) {
  let file = null;
  let asJson = false;
  let asYaml = false;
  let get = null;

  for (let index = 0; index < argv.length; index++) {
    const argument = argv[index];
    if (argument === "-h" || argument === "--help") {
      io.out(USAGE);
      return 0;
    }
    if (argument === "--json") {
      asJson = true;
      continue;
    }
    if (argument === "--yaml") {
      asYaml = true;
      continue;
    }
    if (argument === "--get") {
      if (index + 1 >= argv.length) {
        io.err("error: --get needs a path");
        return 2;
      }
      get = argv[++index];
      continue;
    }
    if (argument === "-") {
      file = null;
      continue;
    }
    if (argument.startsWith("-")) {
      io.err(`error: unknown option '${argument}'`);
      io.err(USAGE);
      return 2;
    }
    if (file !== null) {
      io.err("error: only one file may be given");
      return 2;
    }
    file = argument;
  }

  let text;
  try {
    text = file === null ? io.readStdin() : io.readFile(file);
  } catch {
    io.err(`error: cannot open '${file}'`);
    return 1;
  }

  try {
    if (asYaml) {
      io.out(stringifyYaml(JSON.parse(text)));
      return 0;
    }
    const value = parseYaml(text);
    if (get !== null) {
      const found = getPath(value, get);
      if (found === undefined) {
        io.err(`error: no value at '${get}'`);
        return 1;
      }
      io.out(typeof found === "object" ? JSON.stringify(found) : String(found));
      return 0;
    }
    io.out(asJson ? JSON.stringify(value, null, 2) : stringifyYaml(value));
    return 0;
  } catch (error) {
    if (error instanceof YamlError || error instanceof SyntaxError) {
      io.err(`error: ${error.message}`);
      return 1;
    }
    throw error;
  }
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  const code = main(process.argv.slice(2), {
    out: (line) => process.stdout.write(`${line}\n`),
    err: (line) => process.stderr.write(`${line}\n`),
    readStdin: () => readFileSync(0, "utf8"),
    readFile: (path) => readFileSync(path, "utf8"),
  });
  process.exit(code);
}
