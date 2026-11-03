// Drives the real entry point as a subprocess: exit codes and stdout only
// count when the shell produced them, not when a function returned them.

import { describe, expect, it } from "bun:test";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const ROOT = join(import.meta.dir, "..");
const BINARY = join(ROOT, "bin", "{{ npm_name }}");

function run(args: string[]) {
  const result = Bun.spawnSync({
    cmd: [BINARY, ...args],
    cwd: ROOT,
    stdout: "pipe",
    stderr: "pipe",
  });
  const decoder = new TextDecoder();
  return {
    code: result.exitCode,
    stdout: decoder.decode(result.stdout),
    stderr: decoder.decode(result.stderr),
  };
}

function fields(output: string): string[] {
  return output.trim().split(/\s+/).filter(Boolean);
}

function withFile(contents: string, body: (path: string) => void): void {
  const dir = mkdtempSync(join(tmpdir(), "textstat-"));
  const path = join(dir, "sample.txt");
  writeFileSync(path, contents);
  try {
    body(path);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

describe("command line", () => {
  it("--help exits 0 and prints a usage line naming the binary", () => {
    const { code, stdout } = run(["--help"]);
    expect(code).toBe(0);
    expect(stdout).toContain("usage: {{ npm_name }}");
  });

  it("an unknown flag exits 2", () => {
    const { code, stderr } = run(["--bogus"]);
    expect(code).toBe(2);
    expect(stderr).toContain("unknown option");
  });

  it("a missing file exits 1", () => {
    const { code, stderr } = run(["does-not-exist.txt"]);
    expect(code).toBe(1);
    expect(stderr).toContain("cannot open");
  });

  it("a directory is a read error, not an empty file", () => {
    const { code, stderr } = run(["."]);
    expect(code).toBe(1);
    expect(stderr).toContain("cannot read");
  });

  it("a file with a trailing newline is counted like wc", () => {
    withFile("hello world\n", (path) => {
      const { code, stdout } = run([path]);
      expect(code).toBe(0);
      expect(fields(stdout)).toEqual(["1", "2", "12", path]);
    });
  });

  it("a file with no trailing newline reports zero lines", () => {
    withFile("hello", (path) => {
      const { code, stdout } = run([path]);
      expect(code).toBe(0);
      expect(fields(stdout)).toEqual(["0", "1", "5", path]);
    });
  });

  it("-l prints only the line count", () => {
    withFile("a\nb\n", (path) => {
      const { code, stdout } = run(["-l", path]);
      expect(code).toBe(0);
      expect(fields(stdout)).toEqual(["2", path]);
    });
  });

  it("standard input is counted when no file is given", () => {
    const result = Bun.spawnSync({
      cmd: ["sh", "-c", `printf 'a b\\n' | '${BINARY}'`],
      cwd: ROOT,
      stdout: "pipe",
      stderr: "pipe",
    });
    const decoder = new TextDecoder();
    expect(result.exitCode).toBe(0);
    expect(fields(decoder.decode(result.stdout))).toEqual(["1", "2", "4"]);
  });

  it("several files print a total", () => {
    const dir = mkdtempSync(join(tmpdir(), "textstat-"));
    const first = join(dir, "first.txt");
    const second = join(dir, "second.txt");
    writeFileSync(first, "a\n");
    writeFileSync(second, "b\n");
    try {
      const { code, stdout } = run([first, second]);
      expect(code).toBe(0);
      const tokens = fields(stdout);
      expect(tokens[tokens.length - 1]).toBe("total");
      expect(tokens[tokens.length - 4]).toBe("2");
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});
