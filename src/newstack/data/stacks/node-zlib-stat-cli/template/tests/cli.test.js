import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { main } from "../src/cli.js";

function memory() {
  const out = [];
  const err = [];
  return {
    io: { out: { write: (s) => out.push(s) }, err: { write: (s) => err.push(s) } },
    out,
    err,
  };
}

test("compress then decompress through the CLI preserves the payload", () => {
  const dir = mkdtempSync(join(tmpdir(), "zstat-"));
  try {
    const source = join(dir, "in.txt");
    const packed = join(dir, "in.gz");
    const restored = join(dir, "out.txt");
    writeFileSync(source, "hello gzip world");
    assert.equal(main(["compress", source, "--out", packed]), 0);
    assert.equal(main(["decompress", packed, "--out", restored]), 0);
    assert.equal(execFileSync("cmp", ["-s", source, restored], { stdio: "ignore" }) ?? "", "");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("stats prints the sizes for a gzip file", () => {
  const dir = mkdtempSync(join(tmpdir(), "zstat-"));
  try {
    const source = join(dir, "in.txt");
    const packed = join(dir, "in.gz");
    writeFileSync(source, "a".repeat(400));
    assert.equal(main(["compress", source, "--out", packed, "--level", "9"]), 0);
    const { io, out } = memory();
    assert.equal(main(["stats", packed], io), 0);
    assert.match(out.join(""), /^input=400 bytes compressed=\d+ bytes ratio=[\d.]+ saved=/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("bad usage exits 2 and writes the reason to stderr", () => {
  const { io, err } = memory();
  assert.equal(main(["compress", "--level", "12"], io), 2);
  assert.match(err.join(""), /--level must be an integer 0\.\.9/);
});

test("a missing file exits 1", () => {
  const { io, err } = memory();
  assert.equal(main(["stats", "/nonexistent/sitemap.gz"], io), 1);
  assert.match(err.join(""), /stats needs a file|ENOENT|nonexistent/);
});

test("no arguments prints usage with exit 2 and --help exits 0", () => {
  const { io, out } = memory();
  assert.equal(main([], io), 2);
  assert.match(out.join(""), /Commands:/);
  const help = memory();
  assert.equal(main(["--help"], help.io), 0);
});
