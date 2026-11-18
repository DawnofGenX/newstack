import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { main } from "../src/cli.ts";

let root = "";

beforeAll(() => {
  root = mkdtempSync(join(tmpdir(), "glob-cli-"));
  mkdirSync(join(root, "src", "deep"), { recursive: true });
  mkdirSync(join(root, "docs"));
  writeFileSync(join(root, "index.ts"), "export {};\n");
  writeFileSync(join(root, "src", "a.ts"), "export {};\n");
  writeFileSync(join(root, "src", "deep", "b.ts"), "export {};\n");
  writeFileSync(join(root, "src", "note.md"), "# note\n");
  writeFileSync(join(root, "docs", "guide.md"), "# guide\n");
});

afterAll(() => {
  rmSync(root, { recursive: true, force: true });
});

function capture(argv: string[]) {
  const out: string[] = [];
  const err: string[] = [];
  return main(argv, { out: (text) => out.push(text), err: (text) => err.push(text) }).then((status) => ({
    status,
    lines: out.join("").split("\n").filter((line) => line !== ""),
    err: err.join(""),
  }));
}

describe("cli", () => {
  test("finds nested files", async () => {
    const result = await capture(["--root", root, "**/*.ts"]);
    expect(result.status).toBe(0);
    expect(result.lines.sort()).toEqual(["index.ts", "src/a.ts", "src/deep/b.ts"]);
  });

  test("a segment pattern respects directories", async () => {
    const result = await capture(["--root", root, "src/*.ts"]);
    expect(result.lines).toEqual(["src/a.ts"]);
  });

  test("--ignore removes matches", async () => {
    const result = await capture(["--root", root, "--ignore", "src/**", "**/*.ts"]);
    expect(result.lines).toEqual(["index.ts"]);
  });

  test("braces match several extensions", async () => {
    const result = await capture(["--root", root, "*.{ts,md}"]);
    expect(result.lines).toEqual(["index.ts"]);
  });

  test("no match exits 1", async () => {
    const result = await capture(["--root", root, "*.rs"]);
    expect(result.status).toBe(1);
    expect(result.err).toContain("no match");
  });

  test("a missing root exits 1", async () => {
    const result = await capture(["--root", join(root, "nope"), "*"]);
    expect(result.status).toBe(1);
  });

  test("bad usage exits 2", async () => {
    expect((await capture([])).status).toBe(2);
    expect((await capture(["--bogus", "*"])).status).toBe(2);
    expect((await capture(["--root"])).status).toBe(2);
  });

  test("--help exits 0", async () => {
    const result = await capture(["--help"]);
    expect(result.status).toBe(0);
    expect(result.lines.join("\n")).toContain("--ignore");
  });

  test("--null separates with NUL", async () => {
    const out: string[] = [];
    await main(["--root", root, "-0", "index.ts"], { out: (text) => out.push(text), err: () => {} });
    expect(out.join("")).toBe("index.ts\0");
  });
});
