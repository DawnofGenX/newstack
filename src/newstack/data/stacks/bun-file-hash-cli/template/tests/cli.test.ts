// Drives the real entry point as a subprocess: exit codes and stdout only count
// when the shell produced them.

import { describe, expect, it } from "bun:test";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const ROOT = join(import.meta.dir, "..");
const BINARY = join(ROOT, "bin", "{{ npm_name }}");

function run(args: string[]) {
  const result = Bun.spawnSync({ cmd: [BINARY, ...args], cwd: ROOT, stdout: "pipe", stderr: "pipe" });
  const decoder = new TextDecoder();
  return { code: result.exitCode, stdout: decoder.decode(result.stdout), stderr: decoder.decode(result.stderr) };
}

function withFile(contents: string, body: (path: string) => void): void {
  const dir = mkdtempSync(join(tmpdir(), "hashsum-"));
  const path = join(dir, "sample.txt");
  writeFileSync(path, contents);
  try {
    body(path);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

describe("command line", () => {
  it("--help exits 0 and names the binary", () => {
    const { code, stdout } = run(["--help"]);
    expect(code).toBe(0);
    expect(stdout).toContain(`usage: {{ npm_name }}`);
  });

  it("no arguments is a usage error", () => {
    expect(run([]).code).toBe(2);
  });

  it("an unknown flag exits 2", () => {
    const { code, stderr } = run(["--bogus"]);
    expect(code).toBe(2);
    expect(stderr).toContain("unknown option");
  });

  it("an unknown algorithm exits 2", () => {
    expect(run(["--algo", "sha512", "x.txt"]).code).toBe(2);
  });

  it("prints sha256 by default", () => {
    withFile("hello", (path) => {
      const { code, stdout } = run([path]);
      expect(code).toBe(0);
      expect(stdout).toBe(
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  " + path + "\n",
      );
    });
  });

  it("--algo switches the digest", () => {
    withFile("hello", (path) => {
      const { stdout } = run(["--algo", "crc32", path]);
      expect(stdout).toBe("3610a686  " + path + "\n");
    });
  });

  it("a missing file exits 1", () => {
    const { code, stderr } = run(["does-not-exist.txt"]);
    expect(code).toBe(1);
    expect(stderr).toContain("cannot open");
  });

  it("a directory is a read error", () => {
    const { code, stderr } = run(["."]);
    expect(code).toBe(1);
    expect(stderr).toContain("cannot read");
  });

  it("--check reports OK and exits 0 for a matching digest", () => {
    withFile("hello", (path) => {
      const dir = mkdtempSync(join(tmpdir(), "sums-"));
      const sums = join(dir, "SUMS");
      writeFileSync(
        sums,
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  " + path + "\n",
      );
      try {
        const { code, stdout } = run(["--check", sums]);
        expect(code).toBe(0);
        expect(stdout).toContain("1 ok, 0 failed");
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    });
  });

  it("--check exits 1 when a digest does not match", () => {
    withFile("hello", (path) => {
      const dir = mkdtempSync(join(tmpdir(), "sums-"));
      const sums = join(dir, "SUMS");
      writeFileSync(sums, "00  " + path + "\n");
      try {
        const { code, stdout } = run(["--check", sums]);
        expect(code).toBe(1);
        expect(stdout).toContain("0 ok, 1 failed");
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    });
  });
});
