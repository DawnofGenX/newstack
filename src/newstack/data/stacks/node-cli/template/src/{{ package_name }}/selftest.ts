import { EXIT_OK, parseArgs, PROGRAM, UsageError, USAGE, VERSION } from "./cli.js";
import { countBytes, Counter } from "./count.js";
import type { Report } from "./format.js";
import { renderJson, renderTable } from "./format.js";

class Checks {
  private failures = 0;
  private total = 0;

  ok(name: string, condition: boolean): void {
    this.total += 1;
    if (condition) {
      console.log(`ok     ${name}`);
    } else {
      this.failures += 1;
      console.log(`FAIL   ${name}`);
    }
  }

  equal(name: string, actual: unknown, expected: unknown): void {
    const shown = `${JSON.stringify(actual)} (want ${JSON.stringify(expected)})`;
    this.ok(`${name}: ${shown}`, Object.is(actual, expected));
  }

  raises(name: string, body: () => unknown, want: string): void {
    try {
      body();
      this.ok(`${name}: nothing raised`, false);
    } catch (error) {
      const text = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
      this.ok(`${name}: ${text}`, text.includes(want));
    }
  }

  finish(): number {
    if (this.failures > 0) {
      console.log(`selftest: ${this.failures} of ${this.total} check(s) failed`);
      return 1;
    }
    console.log(`selftest: ${this.total} checks passed`);
    return EXIT_OK;
  }
}

function feed(...chunks: Uint8Array[]) {
  const counter = new Counter();
  for (const chunk of chunks) counter.push(chunk);
  return counter.end();
}

export function runSelftest(): number {
  const checks = new Checks();
  const utf8 = (text: string) => new TextEncoder().encode(text);

  const empty = countBytes(new Uint8Array());
  checks.equal("an empty stream has no lines", empty.lines, 0);
  checks.equal("an empty stream has no words", empty.words, 0);
  checks.equal("an empty stream has no bytes", empty.bytes, 0);

  const one = countBytes(utf8("hello world\n"));
  checks.equal("one line", one.lines, 1);
  checks.equal("two words", one.words, 2);
  checks.equal("bytes are utf-8 bytes", one.bytes, 12);

  checks.equal("a last line without a newline still counts", countBytes(utf8("a\nb")).lines, 2);
  checks.equal("a trailing newline does not add a line", countBytes(utf8("a\nb\n")).lines, 2);
  checks.equal("crlf counts like lf", countBytes(utf8("a\r\nb\r\n")).lines, 2);
  checks.equal("crlf is not a word", countBytes(utf8("a\r\nb\r\n")).words, 2);

  const multibyte = utf8("héllo\n");
  checks.equal("a multibyte line is measured in bytes", countBytes(multibyte).bytes, 7);
  checks.equal("a multibyte line is one word", countBytes(multibyte).words, 1);
  checks.equal(
    "a character split across chunks stays one word",
    feed(multibyte.slice(0, 2), multibyte.slice(2)).words,
    1,
  );

  const words = utf8("one two");
  checks.equal("a word split across chunks is not two words", feed(words.slice(0, 5), words.slice(5)).words, 2);
  checks.equal("and the bytes still add up", feed(words.slice(0, 5), words.slice(5)).bytes, 7);

  const used = new Counter();
  used.push(utf8("x"));
  used.end();
  checks.raises("a counter refuses a chunk after end()", () => used.push(utf8("y")), "push() after end()");
  checks.raises("a counter refuses a second end()", () => used.end(), "end() twice");

  checks.equal("--json is understood", parseArgs(["--json", "a.txt"]).json, true);
  checks.equal("a file name is an operand", parseArgs(["a.txt"]).paths.length, 1);
  checks.equal("dash is standard input", parseArgs(["-"]).paths[0], "-");
  checks.equal("-- makes a flag-looking name an operand", parseArgs(["--", "-x"]).paths[0], "-x");
  checks.raises("an unknown flag is refused", () => parseArgs(["--jsn"]), "unknown option --jsn");
  checks.raises("a misspelled flag does not become a path", () => parseArgs(["--fai-empty"]), "unknown option");

  const report: Report = {
    files: [
      { path: "a", lines: 2, words: 3, bytes: 10 },
      { path: "b", lines: 1, words: 1, bytes: 4 },
    ],
    total: { lines: 3, words: 4, bytes: 14 },
  };
  const table = renderTable(report);
  checks.ok("the table names its columns", table.startsWith("lines words bytes"));
  checks.ok("the table totals several files", table.includes("total"));
  const single = renderTable({ files: [report.files[0]!], total: report.files[0]! });
  checks.ok("one file needs no total row", !single.includes("total"));
  const broken = renderTable({
    files: [{ path: "gone", lines: 0, words: 0, bytes: 0, error: "ENOENT" }],
    total: { lines: 0, words: 0, bytes: 0 },
  });
  checks.ok("an unreadable file is shown as ?, not zero", broken.includes("?"));
  checks.ok("and the reason travels with the row", broken.includes("ENOENT"));
  checks.ok("the json is parseable", JSON.parse(renderJson(report)).total.lines === 3);

  checks.ok("the usage text names the program", USAGE.includes(PROGRAM));
  checks.ok("the version is not empty", VERSION.length > 0);

  return checks.finish();
}
