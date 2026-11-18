/**
 * argv handling for {{ npm_name }}: read TOML, print JSON, or pull one dotted
 * key out of it. Everything the CLI can do, the library can do too; this file
 * only decides exit codes and formatting.
 */
import { readFileSync } from "node:fs";
import { flatten, getPath, parseToml, TomlError } from "./toml/toml.ts";

const USAGE = `{{ npm_name }} — read TOML from a file or stdin

Usage:
  {{ npm_name }} [options] [FILE]

Reads FILE, or stdin when FILE is missing or "-".

Options:
  -g, --get KEY     print only this dotted key (a.b, list[0].name)
  -f, --flatten     print one dotted key=value per line instead of JSON
  -h, --help        show this help
`;

export interface Io {
  out: (text: string) => void;
  err: (text: string) => void;
  readStdin: () => string;
}

const defaultIo: Io = {
  out: (text) => process.stdout.write(text),
  err: (text) => process.stderr.write(text),
  readStdin: () => readFileSync(0, "utf8"),
};

export async function main(argv: string[], io: Io = defaultIo): Promise<number> {
  let get: string | undefined;
  let flattenOutput = false;
  const positional: string[] = [];

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i] as string;
    if (arg === "-h" || arg === "--help") {
      io.out(USAGE);
      return 0;
    }
    if (arg === "-g" || arg === "--get") {
      const value = argv[i + 1];
      if (value === undefined) {
        io.err("{{ npm_name }}: --get needs a key\n");
        return 2;
      }
      get = value;
      i += 1;
      continue;
    }
    if (arg.startsWith("--get=")) {
      get = arg.slice("--get=".length);
      continue;
    }
    if (arg === "-f" || arg === "--flatten") {
      flattenOutput = true;
      continue;
    }
    if (arg.startsWith("-") && arg !== "-") {
      io.err(`{{ npm_name }}: unknown option ${arg}\n`);
      return 2;
    }
    positional.push(arg);
  }

  if (positional.length > 1) {
    io.err("{{ npm_name }}: expected at most one file\n");
    return 2;
  }

  const source = positional[0];
  let text: string;
  if (source === undefined || source === "-") {
    text = io.readStdin();
  } else {
    try {
      text = readFileSync(source, "utf8");
    } catch {
      io.err(`{{ npm_name }}: cannot read ${source}\n`);
      return 1;
    }
  }

  let document;
  try {
    document = parseToml(text);
  } catch (error) {
    if (error instanceof TomlError) {
      io.err(`{{ npm_name }}: ${error.message}\n`);
      return 1;
    }
    throw error;
  }

  if (get !== undefined) {
    const value = getPath(document, get);
    if (value === undefined) {
      io.err(`{{ npm_name }}: no such key: ${get}\n`);
      return 1;
    }
    if (typeof value === "object" && value !== null) {
      io.out(`${JSON.stringify(value, null, 2)}\n`);
    } else if (typeof value === "string") {
      io.out(`${value}\n`);
    } else {
      io.out(`${String(value)}\n`);
    }
    return 0;
  }

  if (flattenOutput) {
    for (const [key, value] of Object.entries(flatten(document))) {
      const rendered = typeof value === "object" && value !== null ? JSON.stringify(value) : String(value);
      io.out(`${key}=${rendered}\n`);
    }
    return 0;
  }

  io.out(`${JSON.stringify(document, null, 2)}\n`);
  return 0;
}
