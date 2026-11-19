// The argv parser: a pure function from strings to a decision.

import type { Figure } from "./counts.ts";

export const VERSION = "0.1.0";

export interface Options {
  figures: Figure[];
  files: string[];
}

export type ParseResult =
  | { ok: true; options: Options }
  | { ok: false; reason: string };

export type Action =
  | { kind: "run"; options: Options }
  | { kind: "help" }
  | { kind: "version" }
  | { kind: "usage"; reason: string };

const LONG: Record<string, Figure> = {
  "--lines": "lines",
  "--words": "words",
  "--bytes": "bytes",
};

export function parseArgs(argv: string[]): Action {
  const figures: Figure[] = [];
  const files: string[] = [];
  let onlyFiles = false;

  const add = (figure: Figure) => {
    if (!figures.includes(figure)) figures.push(figure);
  };

  for (const argument of argv) {
    if (onlyFiles) {
      files.push(argument);
      continue;
    }
    if (argument === "--") {
      onlyFiles = true;
      continue;
    }
    if (argument === "-h" || argument === "--help") return { kind: "help" };
    if (argument === "-V" || argument === "--version") return { kind: "version" };
    if (argument in LONG) {
      add(LONG[argument]);
      continue;
    }
    if (argument.startsWith("--")) {
      return { kind: "usage", reason: `unknown option: ${argument}` };
    }
    if (argument.length > 1 && argument.startsWith("-")) {
      for (const letter of argument.slice(1)) {
        if (letter === "l") add("lines");
        else if (letter === "w") add("words");
        else if (letter === "c") add("bytes");
        else return { kind: "usage", reason: `unknown option: -${letter}` };
      }
      continue;
    }
    files.push(argument);
  }

  return {
    kind: "run",
    options: { figures: figures.length ? figures : ["lines", "words", "bytes"], files },
  };
}

export function usage(program: string): string {
  return [
    `usage: ${program} [-l] [-w] [-c] [FILE ...]`,
    "",
    "Count lines, words and bytes in each FILE, or in standard input.",
    "",
    "  -l, --lines    print the line count",
    "  -w, --words    print the word count",
    "  -c, --bytes    print the byte count",
    "  -h, --help     show this message",
    "  -V, --version  show the version",
    "",
    "With no figure flags, all three are printed.  A FILE of - means standard",
    "input; with no FILE at all, standard input is counted.",
    "",
  ].join("\n");
}
