// Everything between the parsed arguments and the outside world: which rows to
// print, how wide the columns are, and which exit code to use.  The IO is a
// small object of functions, so the tests hand it in-memory files.

import { add, columns, countBytes, type Counts, type Figure } from "./counts.ts";
import { parseArgs, usage, VERSION } from "./options.ts";

export const EXIT_OK = 0;
export const EXIT_UNREADABLE = 1;
export const EXIT_USAGE = 2;

export interface IO {
  readFile(path: string): Uint8Array | null;
  readStdin(): Uint8Array;
  out(text: string): void;
  err(text: string): void;
}

interface Row {
  label: string;
  counts: Counts;
}

function width(figures: Figure[], rows: Row[]): number {
  let widest = 1;
  for (const row of rows) {
    for (const value of columns(figures, row.counts)) {
      widest = Math.max(widest, String(value).length);
    }
  }
  return widest;
}

function formatRow(figures: Figure[], counts: Counts, label: string, pad: number): string {
  const cells = columns(figures, counts).map((value) => String(value).padStart(pad, " "));
  return `${cells.join(" ")} ${label}`;
}

export function run(argv: string[], io: IO, program: string): number {
  const action = parseArgs(argv);
  if (action.kind === "help") {
    io.out(usage(program));
    return EXIT_OK;
  }
  if (action.kind === "version") {
    io.out(`${program} ${VERSION}\n`);
    return EXIT_OK;
  }
  if (action.kind === "usage") {
    io.err(`${program}: ${action.reason}\n`);
    io.err(`Try '${program} --help' for more information.\n`);
    return EXIT_USAGE;
  }

  const { figures, files } = action.options;
  const operands = files.length ? files : ["-"];

  // Read everything first: a row is printed only for what could be read, a
  // failure sets the exit code, and one bad file does not hide the others.
  const rows: Row[] = [];
  for (const path of operands) {
    if (path === "-") {
      rows.push({ label: "-", counts: countBytes(io.readStdin()) });
      continue;
    }
    const data = io.readFile(path);
    if (data === null) {
      io.err(`error: cannot open '${path}'\n`);
      continue;
    }
    rows.push({ label: path, counts: countBytes(data) });
  }

  if (rows.length === 0) return EXIT_UNREADABLE;

  const pad = width(figures, rows);
  const total = rows.reduce<Counts>((sum, row) => add(sum, row.counts), {
    lines: 0,
    words: 0,
    bytes: 0,
  });

  for (const row of rows) io.out(`${formatRow(figures, row.counts, row.label, pad)}\n`);
  if (operands.length > 1) io.out(`${formatRow(figures, total, "total", pad)}\n`);

  return rows.length === operands.length ? EXIT_OK : EXIT_UNREADABLE;
}
