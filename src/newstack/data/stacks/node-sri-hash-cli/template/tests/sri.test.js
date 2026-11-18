import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { sriFor, parseSri, verify, verifyManifest } from "../src/sri.js";

const HELLO_SHA384 = "sha384-WeF0h3dEjGnea4ANejO7+5/xtGPkQ1TDVTvNucZm+pASWjx5+QOXvfX2oT3oKGhP";
const HELLO_SHA256 = "sha256-LPJNul+wow4m6DsqxbninhsWHlwfp0JecwQzYpOLmCQ=";

test("pins known digests for hello", () => {
  assert.equal(sriFor(Buffer.from("hello")), HELLO_SHA384);
  assert.equal(sriFor(Buffer.from("hello"), "sha256"), HELLO_SHA256);
});

test("rejects unknown algorithms", () => {
  assert.throws(() => sriFor(Buffer.from("x"), "md5"), /unsupported algorithm: md5/);
  assert.throws(() => parseSri("md5-abc"), /unsupported algorithm: md5/);
  assert.throws(() => parseSri("nodash"), /malformed integrity token/);
});

test("parses multi token integrity", () => {
  const tokens = parseSri(`${HELLO_SHA384} ${HELLO_SHA256}`);
  assert.deepEqual(tokens.map((t) => t.algorithm), ["sha384", "sha256"]);
});

test("verifies any matching token", () => {
  assert.equal(verify(Buffer.from("hello"), HELLO_SHA384), true);
  assert.equal(verify(Buffer.from("hello"), `${HELLO_SHA384} ${HELLO_SHA256}`), true);
  assert.equal(verify(Buffer.from("hello!"), HELLO_SHA384), false);
});

test("verify rejects empty integrity", () => {
  assert.throws(() => verify(Buffer.from("hello"), "  "), /no integrity tokens/);
});

test("verifyManifest reports per file results", () => {
  const dir = mkdtempSync(join(tmpdir(), "sri-"));
  writeFileSync(join(dir, "a.txt"), "hello");
  writeFileSync(join(dir, "b.txt"), "tampered");
  const results = verifyManifest(dir, { "a.txt": HELLO_SHA384, "b.txt": HELLO_SHA384 });
  assert.deepEqual(results, [
    { file: "a.txt", ok: true },
    { file: "b.txt", ok: false },
  ]);
});

test("cli hash, verify and manifest exit codes", () => {
  const dir = mkdtempSync(join(tmpdir(), "sri-"));
  writeFileSync(join(dir, "a.txt"), "hello");
  const hash = spawnSync(process.execPath, ["src/cli.js", "hash", join(dir, "a.txt")], { encoding: "utf8" });
  assert.equal(hash.status, 0, hash.stderr);
  assert.ok(hash.stdout.startsWith(HELLO_SHA384), hash.stdout);

  const ok = spawnSync(process.execPath, ["src/cli.js", "verify", join(dir, "a.txt"), HELLO_SHA384], { encoding: "utf8" });
  assert.equal(ok.status, 0);
  assert.equal(ok.stdout.trim(), "ok");

  writeFileSync(join(dir, "a.txt"), "hello!");
  const bad = spawnSync(process.execPath, ["src/cli.js", "verify", join(dir, "a.txt"), HELLO_SHA384], { encoding: "utf8" });
  assert.equal(bad.status, 1);
  assert.equal(bad.stdout.trim(), "fail");

  const manifestPath = join(dir, "sri.json");
  writeFileSync(manifestPath, JSON.stringify({ "a.txt": HELLO_SHA384 }));
  const manifest = spawnSync(process.execPath, ["src/cli.js", "manifest", manifestPath], { encoding: "utf8" });
  assert.equal(manifest.status, 1);
  assert.deepEqual(JSON.parse(manifest.stdout), [{ file: "a.txt", ok: false }]);
});
