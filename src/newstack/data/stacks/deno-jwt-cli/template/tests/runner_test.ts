import { run, type IO } from "../src/runner.ts";

interface Captured {
  code: number;
  out: string;
  err: string;
}

const encoder = new TextEncoder();

function capture(argv: string[], files: Record<string, string> = {}, stdin = ""): Captured {
  let out = "";
  let err = "";
  const io: IO = {
    readFile: (path) => (path in files ? encoder.encode(files[path]) : null),
    readStdin: () => encoder.encode(stdin),
    out: (text) => {
      out += text;
    },
    err: (text) => {
      err += text;
    },
  };
  const code = run(argv, io, "proj");
  return { code, out, err };
}

function equal(actual: unknown, expected: unknown): void {
  const left = JSON.stringify(actual);
  const right = JSON.stringify(expected);
  if (left !== right) throw new Error(`got ${left}, want ${right}`);
}

const FILES = { "a.txt": "alpha beta\ngamma\n", "b.txt": "one\n" };

Deno.test("counts a file", () => {
  equal(capture(["a.txt"], FILES), { code: 0, out: " 2  3 17 a.txt\n", err: "" });
});

Deno.test("one figure has no padding", () => {
  equal(capture(["-w", "a.txt"], FILES), { code: 0, out: "3 a.txt\n", err: "" });
});

Deno.test("two files add a total row", () => {
  equal(capture(["a.txt", "b.txt"], FILES), {
    code: 0,
    out: " 2  3 17 a.txt\n 1  1  4 b.txt\n 3  4 21 total\n",
    err: "",
  });
});

Deno.test("stdin is counted when no file is named", () => {
  equal(capture([], {}, "alpha beta\ngamma\n"), { code: 0, out: " 2  3 17 -\n", err: "" });
});

Deno.test("stdin with a figure flag", () => {
  equal(capture(["-w"], {}, "alpha beta\ngamma\n"), { code: 0, out: "3 -\n", err: "" });
});

Deno.test("an unreadable operand sets the exit code but not the others", () => {
  equal(capture(["a.txt", "missing.txt"], FILES), {
    code: 1,
    out: " 2  3 17 a.txt\n 2  3 17 total\n",
    err: "error: cannot open 'missing.txt'\n",
  });
});

Deno.test("nothing readable is still exit 1", () => {
  equal(capture(["missing.txt"]), {
    code: 1,
    out: "",
    err: "error: cannot open 'missing.txt'\n",
  });
});

Deno.test("help and version exit 0", () => {
  const help = capture(["--help"]);
  equal(help.code, 0);
  if (!help.out.startsWith("usage: proj")) throw new Error("help text changed shape");
  equal(capture(["--version"]), { code: 0, out: "proj 0.1.0\n", err: "" });
});

Deno.test("a usage error exits 2", () => {
  equal(capture(["--bogus"]), {
    code: 2,
    out: "",
    err: "proj: unknown option: --bogus\nTry 'proj --help' for more information.\n",
  });
});
