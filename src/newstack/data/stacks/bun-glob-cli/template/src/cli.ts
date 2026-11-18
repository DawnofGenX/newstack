/**
 * argv handling for {{ npm_name }}: walk a directory and print the entries that
 * match a pattern. Matching lives in src/glob/glob.ts; this file only touches
 * the filesystem and decides exit codes.
 */
import { readdirSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { matches, matchesAny, normalise } from "./glob/glob.ts";

const USAGE = `{{ npm_name }} — match paths against a glob pattern

Usage:
  {{ npm_name }} [options] PATTERN

Walks the root directory and prints every path that matches PATTERN.
Patterns support *, **, ?, [abc], [!abc] and {a,b}.

Options:
  -r, --root DIR      directory to search (default ".")
  -i, --ignore GLOB   skip matching paths; repeatable
  -d, --dirs          print directories too
  -0, --null          separate results with NUL instead of a newline
  -h, --help          show this help
`;

export interface Io {
  out: (text: string) => void;
  err: (text: string) => void;
}

const defaultIo: Io = {
  out: (text) => process.stdout.write(text),
  err: (text) => process.stderr.write(text),
};

/** Every file under `root`, as paths relative to it, sorted. */
export function walk(root: string, dirs = false): string[] {
  const found: string[] = [];
  const visit = (dir: string): void => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      if (entry.name === ".git" || entry.name === "node_modules") continue;
      const absolute = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (dirs) found.push(normalise(relative(root, absolute)));
        visit(absolute);
        continue;
      }
      found.push(normalise(relative(root, absolute)));
    }
  };
  visit(root);
  return found.sort();
}

export async function main(argv: string[], io: Io = defaultIo): Promise<number> {
  let root = ".";
  let dirs = false;
  let separator = "\n";
  const ignores: string[] = [];
  const positional: string[] = [];

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i] as string;
    if (arg === "-h" || arg === "--help") {
      io.out(USAGE);
      return 0;
    }
    if (arg === "-r" || arg === "--root") {
      const value = argv[i + 1];
      if (value === undefined) {
        io.err("{{ npm_name }}: --root needs a directory\n");
        return 2;
      }
      root = value;
      i += 1;
      continue;
    }
    if (arg.startsWith("--root=")) {
      root = arg.slice("--root=".length);
      continue;
    }
    if (arg === "-i" || arg === "--ignore") {
      const value = argv[i + 1];
      if (value === undefined) {
        io.err("{{ npm_name }}: --ignore needs a pattern\n");
        return 2;
      }
      ignores.push(value);
      i += 1;
      continue;
    }
    if (arg.startsWith("--ignore=")) {
      ignores.push(arg.slice("--ignore=".length));
      continue;
    }
    if (arg === "-d" || arg === "--dirs") {
      dirs = true;
      continue;
    }
    if (arg === "-0" || arg === "--null") {
      separator = "\0";
      continue;
    }
    if (arg.startsWith("-") && arg !== "-") {
      io.err(`{{ npm_name }}: unknown option ${arg}\n`);
      return 2;
    }
    positional.push(arg);
  }

  if (positional.length !== 1) {
    io.err("{{ npm_name }}: expected exactly one pattern\n");
    return 2;
  }

  const pattern = positional[0] as string;
  const base = resolve(root);

  let entries: string[];
  try {
    entries = walk(base, dirs);
  } catch {
    io.err(`{{ npm_name }}: cannot read ${root}\n`);
    return 1;
  }

  const hits = entries.filter(
    (path) => matches(pattern, path) && !(ignores.length > 0 && matchesAny(ignores, path)),
  );

  if (hits.length === 0) {
    io.err("{{ npm_name }}: no match\n");
    return 1;
  }

  for (const path of hits) {
    io.out(path + separator);
  }
  return 0;
}
