import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { EXIT_GATE, EXIT_OK, EXIT_USAGE, parseArgs, UsageError } from "../src/{{ package_name }}/cli.js";

const ENTRY = new URL("../src/{{ package_name }}/main.js", import.meta.url).pathname;

interface Run {
  status: number | null;
  stdout: string;
  stderr: string;
}

function run(args: readonly string[], input?: string): Run {
  const child = spawnSync(process.execPath, [ENTRY, ...args], {
    input,
    encoding: "utf8",
  });
  return { status: child.status, stdout: child.stdout, stderr: child.stderr };
}

function workspace(): { dir: string; write: (name: string, body: string) => string } {
  const dir = mkdtempSync(join(tmpdir(), "cli-test-"));
  return {
    dir,
    write: (name, body) => {
      const path = join(dir, name);
      writeFileSync(path, body);
      return path;
    },
  };
}

test("parseArgs understands the flags it documents", () => {
  assert.deepEqual(parseArgs(["--json", "--fail-empty", "a"]), {
    mode: "run",
    json: true,
    failEmpty: true,
    paths: ["a"],
  });
  assert.equal(parseArgs(["--help"]).mode, "help");
  assert.equal(parseArgs(["-V"]).mode, "version");
  assert.equal(parseArgs(["--selftest"]).mode, "selftest");
});

test("parseArgs refuses a flag it does not know", () => {
  assert.throws(() => parseArgs(["--jsn"]), UsageError);
  assert.throws(() => parseArgs(["-x"]), /unknown option -x/);
});

test("-- ends the flags", () => {
  assert.deepEqual(parseArgs(["--", "--json"]).paths, ["--json"]);
  assert.equal(parseArgs(["--", "--json"]).json, false);
});

test("a file is counted and the table names it", () => {
  const room = workspace();
  try {
    const path = room.write("a.txt", "hello world\nbye\n");
    const result = run([path]);
    assert.equal(result.status, EXIT_OK);
    assert.match(result.stdout, /a\.txt/);
    assert.match(result.stdout, /^\s*2\s+3\s+16/m);
    assert.equal(result.stderr, "");
  } finally {
    rmSync(room.dir, { recursive: true, force: true });
  }
});

test("--json is one parseable object", () => {
  const room = workspace();
  try {
    const path = room.write("a.txt", "hello\n");
    const result = run(["--json", path]);
    assert.equal(result.status, EXIT_OK);
    const report = JSON.parse(result.stdout);
    assert.equal(report.files[0].lines, 1);
    assert.equal(report.total.words, 1);
  } finally {
    rmSync(room.dir, { recursive: true, force: true });
  }
});

test("standard input is read when no file is named", () => {
  const result = run([], "one two three\n");
  assert.equal(result.status, EXIT_OK);
  assert.match(result.stdout, /^\s*1\s+3\s+14/m);
});

test("a piped - is the same thing", () => {
  const result = run(["-"], "one two\n");
  assert.equal(result.status, EXIT_OK);
  assert.match(result.stdout, /2\s+\s*8/);
});

test("an unreadable file is reported and changes the exit code", () => {
  const result = run(["/definitely/not/here"]);
  assert.equal(result.status, EXIT_GATE);
  assert.match(result.stderr, /ENOENT/);
});

test("--fail-empty turns zero lines into a failure", () => {
  assert.equal(run(["--fail-empty"], "").status, EXIT_GATE);
  assert.match(run(["--fail-empty"], "").stderr, /no lines counted/);
  assert.equal(run(["--fail-empty"], "x\n").status, EXIT_OK);
});

test("bad usage exits 2 and prints the usage text", () => {
  const result = run(["--nope"]);
  assert.equal(result.status, EXIT_USAGE);
  assert.match(result.stderr, /unknown option --nope/);
  assert.match(result.stderr, /usage:/);
});

test("standard input is refused twice", () => {
  const result = run(["-", "-"], "");
  assert.equal(result.status, EXIT_USAGE);
  assert.match(result.stderr, /read once/);
});

test("--help and --version succeed on stdout", () => {
  const help = run(["--help"]);
  assert.equal(help.status, EXIT_OK);
  assert.match(help.stdout, /usage:/);
  const version = run(["--version"]);
  assert.equal(version.status, EXIT_OK);
  assert.match(version.stdout, /^\S+ \d+\.\d+\.\d+$/m);
});

test("the selftest passes", () => {
  const result = run(["--selftest"]);
  assert.equal(result.status, EXIT_OK);
  assert.match(result.stdout, /checks passed/);
});
