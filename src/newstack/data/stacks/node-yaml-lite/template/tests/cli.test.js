import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { main } from "../src/cli.js";

function harness(input, files = {}) {
  const out = [];
  const err = [];
  const io = {
    out: (line) => out.push(line),
    err: (line) => err.push(line),
    readStdin: () => input,
    readFile: (path) => {
      if (!Object.hasOwn(files, path)) {
        throw new Error("missing");
      }
      return files[path];
    },
  };
  return { io, out, err };
}

test("--json prints parsed JSON", () => {
  const { io, out } = harness("a: 1\n");
  assert.equal(main(["--json"], io), 0);
  assert.deepEqual(JSON.parse(out.join("\n")), { a: 1 });
});

test("--get prints one value", () => {
  const { io, out } = harness("server:\n  port: 8080\n");
  assert.equal(main(["--get", "server.port"], io), 0);
  assert.deepEqual(out, ["8080"]);
});

test("--get on a missing path exits 1", () => {
  const { io, err } = harness("a: 1\n");
  assert.equal(main(["--get", "b.c"], io), 1);
  assert.match(err[0], /no value at 'b.c'/);
});

test("--yaml reads JSON and prints YAML", () => {
  const { io, out } = harness('{"a":{"b":2}}');
  assert.equal(main(["--yaml"], io), 0);
  assert.equal(out[0], "a:\n  b: 2");
});

test("a parse error exits 1", () => {
  const { io, err } = harness("a: |\n  x\n");
  assert.equal(main([], io), 1);
  assert.match(err[0], /block scalars/);
});

test("an unknown option exits 2", () => {
  const { io, err } = harness("");
  assert.equal(main(["--bogus"], io), 2);
  assert.match(err[0], /unknown option/);
});

test("help exits 0", () => {
  const { io, out } = harness("");
  assert.equal(main(["--help"], io), 0);
  assert.match(out[0], /usage: /);
});

test("reads a named file", () => {
  const { io, out } = harness("", { "cfg.yaml": "name: demo\n" });
  assert.equal(main(["cfg.yaml", "--json"], io), 0);
  assert.deepEqual(JSON.parse(out.join("\n")), { name: "demo" });
});

test("an unreadable file exits 1", () => {
  const { io, err } = harness("", {});
  assert.equal(main(["missing.yaml"], io), 1);
  assert.match(err[0], /cannot open/);
});
