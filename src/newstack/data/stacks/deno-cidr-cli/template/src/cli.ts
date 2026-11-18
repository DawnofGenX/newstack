import { Cidr, CidrError, contains, describe, parseCidr } from "./cidr.ts";

/** Where the CLI writes and reads, injected so tests never touch the process. */
export interface Io {
  out: (line: string) => void;
  err: (line: string) => void;
  readStdin: () => Promise<string>;
  readFile: (path: string) => Promise<string>;
}

/** The parsed command line. */
export interface Options {
  files: string[];
  json: boolean;
  contains: string | null;
  status: "ok" | "help" | "error";
  error?: string;
}

export const usage = `usage: deno-cidr-cli [--json] [--contains ADDRESS] [FILE ...]

Reads CIDR blocks, one per line, from the files or from standard input.

  --json               print a JSON array instead of a table
  --contains ADDRESS   only report blocks that contain ADDRESS
  -h, --help           print this message

Exit status is 1 for an unreadable file or a bad block and 2 for bad usage.`;

/** Parses argv without a dependency so every branch is unit tested. */
export function parseArgs(argv: string[]): Options {
  const files: string[] = [];
  let json = false;
  let containsAddress: string | null = null;
  let onlyFiles = false;

  for (let index = 0; index < argv.length; index++) {
    const argument = argv[index];
    if (onlyFiles || argument === "-") {
      files.push(argument);
      continue;
    }
    if (argument === "--") {
      onlyFiles = true;
      continue;
    }
    if (argument === "-h" || argument === "--help") {
      return { files, json, contains: containsAddress, status: "help" };
    }
    if (argument === "--json") {
      json = true;
      continue;
    }
    if (argument === "--contains") {
      const value = argv[index + 1];
      if (value === undefined) {
        return {
          files,
          json,
          contains: null,
          status: "error",
          error: "option --contains needs a value",
        };
      }
      containsAddress = value;
      index++;
      continue;
    }
    if (argument.startsWith("-")) {
      return {
        files,
        json,
        contains: null,
        status: "error",
        error: `unknown option '${argument}'`,
      };
    }
    files.push(argument);
  }

  return { files, json, contains: containsAddress, status: "ok" };
}

/** Runs the CLI and returns the exit code. */
export async function main(argv: string[], io: Io): Promise<number> {
  const options = parseArgs(argv);

  if (options.status === "help") {
    io.out(usage);
    return 0;
  }
  if (options.status === "error") {
    io.err(`error: ${options.error}`);
    io.err(usage);
    return 2;
  }

  const text = options.files.length === 0
    ? await io.readStdin()
    : await readAll(options.files, io);
  if (text === null) {
    return 1;
  }

  const blocks: Cidr[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (line === "" || line.startsWith("#")) {
      continue;
    }
    try {
      const block = parseCidr(line);
      if (options.contains !== null && !contains(block, options.contains)) {
        continue;
      }
      blocks.push(block);
    } catch (error) {
      if (error instanceof CidrError) {
        io.err(`error: ${error.message}`);
        return 1;
      }
      throw error;
    }
  }

  if (options.json) {
    const payload = blocks.map((block) => ({
      block: `${describe(block).split(" ")[0]}`,
      network: block.network,
      broadcast: block.broadcast,
      prefix: block.prefix,
      hosts: Math.max(0, block.size - (block.prefix >= 31 ? 0 : 2)),
    }));
    io.out(JSON.stringify(payload, null, 2));
    return 0;
  }

  if (blocks.length === 0) {
    io.out("no blocks matched");
    return 0;
  }
  for (const block of blocks) {
    io.out(describe(block));
  }
  return 0;
}

async function readAll(files: string[], io: Io): Promise<string | null> {
  const parts: string[] = [];
  for (const path of files) {
    if (path === "-") {
      parts.push(await io.readStdin());
      continue;
    }
    try {
      parts.push(await io.readFile(path));
    } catch {
      io.err(`error: cannot open '${path}'`);
      return null;
    }
  }
  return parts.join("\n");
}
