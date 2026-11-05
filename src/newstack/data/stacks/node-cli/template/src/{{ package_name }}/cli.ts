import { createReadStream } from "node:fs";
import { add, Counter, ZERO } from "./count.js";
import type { Counts, FileCounts, Report } from "./format.js";
import { renderJson, renderTable } from "./format.js";
import { runSelftest } from "./selftest.js";

export const PROGRAM = "{{ npm_name }}";
export const VERSION = "0.1.0";

export const EXIT_OK = 0;
/** A file could not be read, or the --fail-empty gate tripped. */
export const EXIT_GATE = 1;
/** The command line was wrong: never a silent default. */
export const EXIT_USAGE = 2;

export class UsageError extends Error {}

export type Mode = "run" | "help" | "version" | "selftest";

export interface Options {
  mode: Mode;
  json: boolean;
  failEmpty: boolean;
  paths: string[];
}

export const USAGE = `usage: ${PROGRAM} [--json] [--fail-empty] [FILE...]

Count lines, words and bytes. With no FILE, or with -, read standard input.

  --json        print one JSON object instead of a table
  --fail-empty  exit 1 when no line was counted (a gate, not a report)
  --help        print this text
  --version     print the version
  --selftest    run the offline checks

exit codes: 0 ok, 1 unreadable file or empty gate, 2 bad usage
`;

/**
 * Every flag is either understood or rejected. A CLI that ignores `--jsn` and
 * prints a table is a CLI that fails in a pipeline three commits later.
 */
export function parseArgs(argv: readonly string[]): Options {
  const options: Options = { mode: "run", json: false, failEmpty: false, paths: [] };
  let operandsOnly = false;
  for (const argument of argv) {
    if (operandsOnly) {
      options.paths.push(argument);
      continue;
    }
    if (argument === "--") {
      operandsOnly = true;
    } else if (argument === "--json") {
      options.json = true;
    } else if (argument === "--fail-empty") {
      options.failEmpty = true;
    } else if (argument === "--help" || argument === "-h") {
      options.mode = "help";
    } else if (argument === "--version" || argument === "-V") {
      options.mode = "version";
    } else if (argument === "--selftest") {
      options.mode = "selftest";
    } else if (argument === "-" || !argument.startsWith("-")) {
      options.paths.push(argument);
    } else {
      throw new UsageError(`unknown option ${argument}`);
    }
  }
  return options;
}

async function countSource(path: string): Promise<FileCounts> {
  const counter = new Counter();
  if (path === "-") {
    for await (const chunk of process.stdin) {
      counter.push(chunk as Uint8Array);
    }
    return { path, ...counter.end() };
  }
  try {
    for await (const chunk of createReadStream(path)) {
      counter.push(chunk as Uint8Array);
    }
  } catch (error) {
    // A count of zero for a file that does not exist is indistinguishable from an
    // empty file, so the failure travels with the row and with the exit code.
    const code = (error as NodeJS.ErrnoException).code ?? "EIO";
    return { path, ...ZERO, error: code };
  }
  return { path, ...counter.end() };
}

function total(files: readonly FileCounts[]): Counts {
  return files.reduce<Counts>((sum, file) => add(sum, file), { ...ZERO });
}

export async function main(argv: readonly string[]): Promise<number> {
  let options: Options;
  try {
    options = parseArgs(argv);
  } catch (error) {
    if (!(error instanceof UsageError)) throw error;
    process.stderr.write(`${PROGRAM}: ${error.message}\n`);
    process.stderr.write(USAGE);
    return EXIT_USAGE;
  }
  if (options.mode === "help") {
    process.stdout.write(USAGE);
    return EXIT_OK;
  }
  if (options.mode === "version") {
    process.stdout.write(`${PROGRAM} ${VERSION}\n`);
    return EXIT_OK;
  }
  if (options.mode === "selftest") {
    return runSelftest();
  }

  const readsStdin = options.paths.filter((path) => path === "-").length;
  if (readsStdin > 1) {
    process.stderr.write(`${PROGRAM}: standard input can only be read once\n`);
    return EXIT_USAGE;
  }
  if (options.paths.length === 0) {
    // Reading a terminal would block until the user presses Ctrl-D with no prompt.
    if (process.stdin.isTTY === true) {
      process.stderr.write(`${PROGRAM}: no input: pass a file or pipe something in\n`);
      process.stderr.write(USAGE);
      return EXIT_USAGE;
    }
    options.paths.push("-");
  }

  const files: FileCounts[] = [];
  for (const path of options.paths) {
    files.push(await countSource(path));
  }
  const report: Report = { files, total: total(files) };

  process.stdout.write(options.json ? renderJson(report) : renderTable(report));
  for (const file of files) {
    if (file.error !== undefined) {
      process.stderr.write(`${PROGRAM}: ${file.path}: ${file.error}\n`);
    }
  }
  if (options.failEmpty && report.total.lines === 0) {
    process.stderr.write(`${PROGRAM}: gate: no lines counted\n`);
    return EXIT_GATE;
  }
  return files.some((file) => file.error !== undefined) ? EXIT_GATE : EXIT_OK;
}
