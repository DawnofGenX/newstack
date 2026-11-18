import { DiffError, diffLines, formatStats, stats, toLines, unifiedBody } from "./diff.ts";

export interface Io {
  out: (line: string) => void;
  err: (line: string) => void;
  readStdin: () => Promise<string>;
  readFile: (path: string) => Promise<string>;
}

export interface Options {
  left: string;
  right: string;
  context: number;
  statOnly: boolean;
  quiet: boolean;
  exitCode: boolean;
  help: boolean;
}

export const USAGE = [
  "usage: diff [options] <left> <right>",
  "",
  "options:",
  "  -U, --unified <n>  lines of context to show (default 3)",
  "      --stat         print only the change counts",
  "  -q, --quiet        print nothing, just set the exit code",
  "      --exit-code    exit 1 when the files differ (0 when identical)",
  "  -h, --help         show this help",
].join("\n");

export class UsageError extends Error {}

export function parseArgs(argv: string[]): Options {
  const options: Options = {
    left: "",
    right: "",
    context: 3,
    statOnly: false,
    quiet: false,
    exitCode: false,
    help: false,
  };
  const positional: string[] = [];
  for (let index = 0; index < argv.length; index++) {
    const arg = argv[index];
    if (arg === "-h" || arg === "--help") {
      options.help = true;
    } else if (arg === "-U" || arg === "--unified") {
      const raw = argv[++index];
      if (raw === undefined) throw new UsageError(`${arg} needs a number`);
      const value = Number(raw);
      if (!Number.isInteger(value) || value < 0) {
        throw new UsageError(`context must be a non-negative integer, got "${raw}"`);
      }
      options.context = value;
    } else if (arg.startsWith("--unified=")) {
      const raw = arg.slice("--unified=".length);
      const value = Number(raw);
      if (!Number.isInteger(value) || value < 0) {
        throw new UsageError(`context must be a non-negative integer, got "${raw}"`);
      }
      options.context = value;
    } else if (arg === "--stat") {
      options.statOnly = true;
    } else if (arg === "-q" || arg === "--quiet") {
      options.quiet = true;
    } else if (arg === "--exit-code") {
      options.exitCode = true;
    } else if (arg.startsWith("-") && arg !== "-") {
      throw new UsageError(`unknown option "${arg}"`);
    } else {
      positional.push(arg);
    }
  }
  if (!options.help) {
    if (positional.length !== 2) {
      throw new UsageError(`expected two files, got ${positional.length}`);
    }
    options.left = positional[0];
    options.right = positional[1];
  }
  return options;
}

async function readPath(path: string, io: Io): Promise<string> {
  if (path === "-") return await io.readStdin();
  try {
    return await io.readFile(path);
  } catch (error) {
    throw new DiffError(`cannot read ${path}: ${(error as Error).message}`);
  }
}

export async function main(argv: string[], io: Io): Promise<number> {
  let options: Options;
  try {
    options = parseArgs(argv);
  } catch (error) {
    if (error instanceof UsageError) {
      io.err(`diff: ${error.message}`);
      io.err(USAGE);
      return 2;
    }
    throw error;
  }
  if (options.help) {
    io.out(USAGE);
    return 0;
  }

  let left: string;
  let right: string;
  let ops;
  try {
    left = await readPath(options.left, io);
    right = await readPath(options.right, io);
    ops = diffLines(toLines(left), toLines(right));
  } catch (error) {
    io.err(`diff: ${(error as Error).message}`);
    return 1;
  }

  const counts = stats(ops);
  const label = `${options.left} -> ${options.right}`;
  if (!options.quiet) {
    if (options.statOnly) {
      io.out(formatStats(label, counts));
    } else if (counts.changed) {
      io.out(`--- ${options.left}`);
      io.out(`+++ ${options.right}`);
      for (const line of unifiedBody(ops, options.context)) io.out(line);
    }
  }

  if (options.exitCode) return counts.changed ? 1 : 0;
  return 0;
}
