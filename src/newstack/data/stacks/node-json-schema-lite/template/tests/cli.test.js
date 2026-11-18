import test from "node:test";
import assert from "node:assert/strict";
import { main } from "../src/cli.js";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const dir = mkdtempSync(join(tmpdir(), "schema-lite-"));
const schemaPath = join(dir, "schema.json");
writeFileSync(schemaPath, JSON.stringify({ type: "object", required: ["name"], properties: { name: { type: "string" } } }));
const goodPath = join(dir, "good.json");
writeFileSync(goodPath, JSON.stringify({ name: "ada" }));
const badPath = join(dir, "bad.json");
writeFileSync(badPath, JSON.stringify({ name: 7 }));

const drive = (argv) => {
  const out = [];
  const err = [];
  const code = main(argv, { out: (line) => out.push(line), err: (line) => err.push(line) });
  return { code, out, err };
};

test("a valid document prints valid and exits 0", () => {
  const { code, out } = drive(["--schema", schemaPath, "--data", goodPath]);
  assert.equal(code, 0);
  assert.deepEqual(out, ["valid"]);
});

test("each problem goes to stderr and the exit code is 1", () => {
  const { code, out, err } = drive(["--schema", schemaPath, "--data", badPath]);
  assert.equal(code, 1);
  assert.deepEqual(out, []);
  assert.deepEqual(err, ["$.name: expected string, got integer"]);
});

test("a missing --schema is a usage error", () => {
  assert.equal(drive(["--data", goodPath]).code, 2);
});

test("an unknown argument is a usage error", () => {
  assert.equal(drive(["--schema", schemaPath, "--verbose"]).code, 2);
});

test("--help prints usage and exits 0", () => {
  const { code, out } = drive(["--help"]);
  assert.equal(code, 0);
  assert.match(out[0], /^usage: /);
});

test("an unreadable schema file exits 1", () => {
  assert.equal(drive(["--schema", join(dir, "missing.json")]).code, 1);
});

test.after(() => rmSync(dir, { recursive: true, force: true }));
