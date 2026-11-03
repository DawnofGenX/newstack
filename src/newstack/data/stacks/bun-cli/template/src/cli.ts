// Entry point: the only file that owns argv, stdout/stderr and the exit code.
// Counting and parsing live in src/textstat/ so tests can drive them directly.

import { add, count, type Counts } from "./textstat/counts.ts";
import { parseArgs, usage, VERSION } from "./textstat/options.ts";

const program = "{{ npm_name }}";

/** Prints the requested figures right-aligned like `wc`, then the label. */
function printCounts(counts: Counts, mode: string, label: string): void {
  const fields: string[] = [];
  if (mode === "all" || mode === "lines") fields.push(String(counts.lines).padStart(8));
  if (mode === "all" || mode === "words") fields.push(String(counts.words).padStart(8));
  if (mode === "all" || mode === "bytes") fields.push(String(counts.bytes).padStart(8));
  const line = label === "" ? fields.join("") : fields.join("") + " " + label;
  process.stdout.write(line + "\n");
}

/** Reads all of standard input as UTF-8 text. */
async function readStdin(): Promise<string> {
  return await Bun.stdin.text();
}

/** Reads one file; the error string is what the CLI reports to stderr. */
async function readPath(path: string): Promise<{ text?: string; error?: string }> {
  let stats;
  try {
    stats = await Bun.file(path).stat();
  } catch {
    return { error: `cannot open '${path}'` };
  }
  if (!stats.isFile()) {
    return { error: `cannot read '${path}'` };
  }
  try {
    return { text: await Bun.file(path).text() };
  } catch {
    return { error: `cannot read '${path}'` };
  }
}

/**
 * Turns argv into output and an exit code: 0 success, 1 unreadable file,
 * 2 bad usage. Nothing here calls process.exit, so `main` stays testable.
 */
export async function main(argv: string[]): Promise<number> {
  const parsed = parseArgs(argv);

  if (!parsed.ok) {
    process.stderr.write(`error: ${parsed.reason}\n\n`);
    process.stderr.write(usage(program));
    return 2;
  }

  const { options } = parsed;

  if (options.help) {
    process.stdout.write(usage(program));
    return 0;
  }
  if (options.version) {
    process.stdout.write(VERSION + "\n");
    return 0;
  }

  if (options.files.length === 0) {
    printCounts(count(await readStdin()), options.mode, "");
    return 0;
  }

  let total: Counts = { lines: 0, words: 0, bytes: 0 };
  let failed = false;

  for (const path of options.files) {
    if (path === "-") {
      const counts = count(await readStdin());
      printCounts(counts, options.mode, "");
      total = add(total, counts);
    } else {
      const result = await readPath(path);
      if (result.error !== undefined) {
        process.stderr.write(`error: ${result.error}\n`);
        failed = true;
      } else {
        const counts = count(result.text ?? "");
        printCounts(counts, options.mode, path);
        total = add(total, counts);
      }
    }
  }

  if (options.files.length > 1) {
    printCounts(total, options.mode, "total");
  }

  return failed ? 1 : 0;
}

// Own the process when run directly (`bun src/cli.ts`); the bin entry point
// calls main() itself.
if (import.meta.main) {
  process.exit(await main(process.argv.slice(2)));
}
