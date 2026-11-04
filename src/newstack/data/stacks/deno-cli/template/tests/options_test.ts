import { parseArgs, usage, VERSION } from "../src/options.ts";

function equal(actual: unknown, expected: unknown, message: string): void {
  const left = JSON.stringify(actual);
  const right = JSON.stringify(expected);
  if (left !== right) throw new Error(`${message}: got ${left}, want ${right}`);
}

const figures = (argv: string[]) => {
  const action = parseArgs(argv);
  if (action.kind !== "run") throw new Error(`expected run, got ${action.kind}`);
  return action.options.figures;
};

const files = (argv: string[]) => {
  const action = parseArgs(argv);
  if (action.kind !== "run") throw new Error(`expected run, got ${action.kind}`);
  return action.options.files;
};

Deno.test("no flags means all three figures", () => {
  equal(figures([]), ["lines", "words", "bytes"], "defaults");
});

Deno.test("flags keep their order and duplicates collapse", () => {
  equal(figures(["-c", "-l"]), ["bytes", "lines"], "order");
  equal(figures(["-l", "-l"]), ["lines"], "duplicates");
  equal(figures(["-lw"]), ["lines", "words"], "clustered");
  equal(figures(["--bytes"]), ["bytes"], "long flag");
});

Deno.test("operands are files, not flags", () => {
  equal(files(["-w", "a.txt", "b.txt"]), ["a.txt", "b.txt"], "operands");
  equal(files(["--", "-l"]), ["-l"], "after the terminator everything is a file");
  equal(files(["-"]), ["-"], "a lone dash is a file");
});

Deno.test("help and version short-circuit", () => {
  equal(parseArgs(["--help"]).kind, "help", "help");
  equal(parseArgs(["-h"]).kind, "help", "-h");
  equal(parseArgs(["--version"]).kind, "version", "version");
  equal(parseArgs(["-V"]).kind, "version", "-V");
  equal(parseArgs(["-w", "--help"]).kind, "help", "help wins over counting");
});

Deno.test("unknown options are usage errors", () => {
  const long = parseArgs(["--bogus"]);
  equal(long, { kind: "usage", reason: "unknown option: --bogus" }, "long");
  const short = parseArgs(["-x"]);
  equal(short, { kind: "usage", reason: "unknown option: -x" }, "short");
});

Deno.test("the version and the usage text agree with the program", () => {
  equal(VERSION, "0.1.0", "version");
  if (!usage("proj").startsWith("usage: proj [-l] [-w] [-c] [FILE ...]")) {
    throw new Error("usage text changed shape");
  }
});
