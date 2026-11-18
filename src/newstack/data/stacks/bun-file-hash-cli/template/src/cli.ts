// Entry point: the only file that owns argv, stdout/stderr and the exit code.

import { readFileSync } from "node:fs";
import { ALGORITHMS, digest, formatLine, parseChecksums, verify, type Algorithm } from "./hash/hash.ts";

const program = "{{ npm_name }}";

function usage(): string {
  return [
    `usage: ${program} [--algo ${ALGORITHMS.join("|")}] FILE ...`,
    `       ${program} [--algo ${ALGORITHMS.join("|")}] -`,
    `       ${program} --check SUMS`,
    "",
    "Print a checksum for each FILE ('-' reads standard input), or verify a",
    "sha256sum-style SUMS file listing digest and file name pairs.",
    "",
    `  --algo NAME    ${ALGORITHMS.join(", ")} (default sha256)`,
    "  --check FILE   verify each line of FILE, exit 1 if any mismatch",
    "  -h, --help     show this help and exit",
    "",
  ].join("\n");
}

async function readBytes(path: string): Promise<Uint8Array | string> {
  if (path === "-") {
    return new Uint8Array(await Bun.stdin.arrayBuffer());
  }
  try {
    const stats = await Bun.file(path).stat();
    if (!stats.isFile()) return `cannot read '${path}'`;
    return new Uint8Array(await Bun.file(path).arrayBuffer());
  } catch {
    return `cannot open '${path}'`;
  }
}

export async function main(argv: string[]): Promise<number> {
  let algorithm: Algorithm = "sha256";
  let check: string | null = null;
  const files: string[] = [];

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "-h" || arg === "--help") {
      process.stdout.write(usage());
      return 0;
    }
    if (arg === "--algo") {
      const value = argv[index + 1];
      if (value === undefined || !(ALGORITHMS as string[]).includes(value)) {
        process.stderr.write(`error: --algo needs one of ${ALGORITHMS.join(", ")}\n`);
        return 2;
      }
      algorithm = value as Algorithm;
      index += 1;
    } else if (arg === "--check") {
      const value = argv[index + 1];
      if (value === undefined) {
        process.stderr.write("error: --check needs a file\n");
        return 2;
      }
      check = value;
      index += 1;
    } else if (arg.startsWith("-") && arg !== "-") {
      process.stderr.write(`error: unknown option '${arg}'\n\n${usage()}`);
      return 2;
    } else {
      files.push(arg);
    }
  }

  if (check !== null) {
    if (files.length > 0) {
      process.stderr.write("error: --check takes no FILE arguments\n");
      return 2;
    }
    return await checkFile(check, algorithm);
  }

  if (files.length === 0) {
    process.stderr.write(usage());
    return 2;
  }

  let failed = false;
  for (const path of files) {
    const bytes = await readBytes(path);
    if (typeof bytes === "string") {
      process.stderr.write(`error: ${bytes}\n`);
      failed = true;
      continue;
    }
    const label = path === "-" ? "-" : path;
    process.stdout.write(formatLine(digest(bytes, algorithm), label) + "\n");
  }
  return failed ? 1 : 0;
}

async function checkFile(path: string, algorithm: Algorithm): Promise<number> {
  let text: string;
  try {
    text = await Bun.file(path).text();
  } catch {
    process.stderr.write(`error: cannot open '${path}'\n`);
    return 1;
  }

  let entries;
  try {
    entries = parseChecksums(text);
  } catch (error) {
    process.stderr.write(`error: ${(error as Error).message}\n`);
    return 1;
  }
  if (entries.length === 0) {
    process.stderr.write(`error: no checksums in '${path}'\n`);
    return 1;
  }

  const cache = new Map<string, string>();
  const actual = (name: string): string => {
    const hit = cache.get(name);
    if (hit !== undefined) return hit;
    let value = "";
    if (name === "-") {
      process.stderr.write("error: cannot verify standard input from a checksum file\n");
    } else {
      try {
        value = digest(new Uint8Array(readFileSync(name)), algorithm);
      } catch {
        process.stderr.write(`error: cannot open '${name}'\n`);
      }
    }
    cache.set(name, value);
    return value;
  };

  const results = verify(entries, actual);
  let failures = 0;
  for (const result of results) {
    if (result.ok) {
      process.stdout.write(`${result.name}: OK\n`);
    } else {
      failures += 1;
      process.stdout.write(`${result.name}: FAILED ${result.expected} != ${result.actual}\n`);
    }
  }
  process.stdout.write(`${results.length - failures} ok, ${failures} failed\n`);
  return failures === 0 ? 0 : 1;
}
