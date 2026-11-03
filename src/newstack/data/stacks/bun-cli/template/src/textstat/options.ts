// Command line parsing: argv in, an options object out. No printing, no
// process.exit, so every branch is a unit test rather than a subprocess.

export type Mode = "all" | "lines" | "words" | "bytes";

export interface Options {
  mode: Mode;
  help: boolean;
  version: boolean;
  files: string[];
}

export type ParseResult =
  | { ok: true; options: Options }
  | { ok: false; reason: string };

export const VERSION = "0.1.0";

const MODES: Record<string, Mode> = {
  "-l": "lines",
  "--lines": "lines",
  "-w": "words",
  "--words": "words",
  "-c": "bytes",
  "--bytes": "bytes",
};

/**
 * The help text. The caller passes the program name so the usage line names
 * the binary that is actually being run.
 */
export function usage(program: string): string {
  return [
    `usage: ${program} [-l | -w | -c] [--] [FILE ...]`,
    "",
    "Count lines, words and bytes in each FILE, or in standard input",
    "when no FILE is given. With more than one FILE a total is printed.",
    "",
    "  -l, --lines     print the line count only",
    "  -w, --words     print the word count only",
    "  -c, --bytes     print the byte count only",
    "  -h, --help      show this help and exit",
    "  -V, --version   show the version and exit",
  ].join("\n") + "\n";
}

/**
 * Parses an argv array (without the program name).
 *
 * Hand-rolled on purpose: one explicit loop keeps `--`, a bare `-` and
 * conflicting modes obvious, and every branch below is pinned by a test.
 */
export function parseArgs(argv: string[]): ParseResult {
  const options: Options = {
    mode: "all",
    help: false,
    version: false,
    files: [],
  };

  let chosen = false;
  let optionsEnded = false;

  for (const value of argv) {
    if (optionsEnded || value === "" || value === "-") {
      options.files.push(value);
    } else if (value === "--") {
      optionsEnded = true;
    } else if (value === "-h" || value === "--help") {
      options.help = true;
      return { ok: true, options };
    } else if (value === "-V" || value === "--version") {
      options.version = true;
      return { ok: true, options };
    } else {
      const mode = MODES[value];
      if (mode !== undefined) {
        if (chosen && options.mode !== mode) {
          return {
            ok: false,
            reason: `choose one of -l, -w, -c: '${value}' conflicts with an earlier mode`,
          };
        }
        chosen = true;
        options.mode = mode;
      } else if (value.startsWith("-")) {
        return { ok: false, reason: `unknown option '${value}'` };
      } else {
        options.files.push(value);
      }
    }
  }

  return { ok: true, options };
}
