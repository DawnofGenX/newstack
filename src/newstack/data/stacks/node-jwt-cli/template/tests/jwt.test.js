import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHmac } from "node:crypto";
import { issue, verify, decode, base64url, base64urlDecode } from "../src/jwt.js";

const SECRET = "unit-test-secret";
const NOW = 1_700_000_000_000;

test("base64url roundtrip and stripping", () => {
  assert.equal(base64url(Buffer.from("hello")), "aGVsbG8");
  assert.equal(base64urlDecode("aGVsbG8").toString("utf8"), "hello");
  assert.ok(!base64url(Buffer.from([0xff, 0xfe])).includes("="));
});

test("issue then verify returns the claims", () => {
  const token = issue({ sub: "alice", role: "admin" }, SECRET, { expiresIn: 60, now: NOW });
  const { header, payload } = verify(token, SECRET, { now: NOW });
  assert.equal(header.alg, "HS256");
  assert.equal(payload.sub, "alice");
  assert.equal(payload.exp, 1_700_000_060);
});

test("expired tokens are rejected unless leeway covers them", () => {
  const token = issue({ sub: "alice" }, SECRET, { expiresIn: 10, now: NOW });
  assert.throws(() => verify(token, SECRET, { now: NOW + 11_000 }), /token expired/);
  assert.doesNotThrow(() => verify(token, SECRET, { now: NOW + 11_000, leeway: 5 }));
});

test("nbf claim gates the token", () => {
  const token = issue({ nbf: Math.floor(NOW / 1000) + 30 }, SECRET, { expiresIn: 600, now: NOW });
  assert.throws(() => verify(token, SECRET, { now: NOW }), /not yet valid/);
  assert.doesNotThrow(() => verify(token, SECRET, { now: NOW + 31_000 }));
});

test("tampered payload and wrong secret fail the signature check", () => {
  const token = issue({ sub: "alice" }, SECRET, { expiresIn: 60, now: NOW });
  const [h, , s] = token.split(".");
  const forged = `${h}.${base64url(JSON.stringify({ sub: "root", exp: 1_700_000_060 }))}.${s}`;
  assert.throws(() => verify(forged, SECRET, { now: NOW }), /signature mismatch/);
  assert.throws(() => verify(token, "other-secret", { now: NOW }), /signature mismatch/);
});

test("alg none and malformed tokens are rejected", () => {
  const header = base64url(JSON.stringify({ alg: "none", typ: "JWT" }));
  const payload = base64url(JSON.stringify({ sub: "alice" }));
  assert.throws(() => verify(`${header}.${payload}.`, SECRET, { now: NOW }), /unsupported alg/);
  assert.throws(() => decode("only.two"), /three segments/);
});

test("decode exposes the header without verifying", () => {
  const token = issue({ sub: "alice" }, SECRET, { expiresIn: 60, now: NOW });
  const parsed = decode(token);
  assert.equal(parsed.header.typ, "JWT");
  assert.equal(parsed.payload.sub, "alice");
  assert.equal(parsed.signature.length > 0, true);
});

test("a token signed by node crypto directly verifies", () => {
  const head = base64url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = base64url(JSON.stringify({ sub: "bob", exp: 1_700_000_100 }));
  const input = `${head}.${body}`;
  const sig = base64url(createHmac("sha256", SECRET).update(input).digest());
  const { payload } = verify(`${input}.${sig}`, SECRET, { now: NOW });
  assert.equal(payload.sub, "bob");
});

test("cli signs and verifies", () => {
  const signed = spawnSync(process.execPath, ["src/cli.js", "sign", "--secret", SECRET, "--payload", '{"sub":"cli"}', "--ttl", "60"], { encoding: "utf8" });
  assert.equal(signed.status, 0, signed.stderr);
  const token = signed.stdout.trim();
  assert.equal(token.split(".").length, 3);
  const verified = spawnSync(process.execPath, ["src/cli.js", "verify", token, "--secret", SECRET], { encoding: "utf8" });
  assert.equal(verified.status, 0, verified.stderr);
  assert.equal(JSON.parse(verified.stdout).sub, "cli");
  const bad = spawnSync(process.execPath, ["src/cli.js", "verify", token, "--secret", "nope"], { encoding: "utf8" });
  assert.equal(bad.status, 1);
  assert.match(bad.stderr, /signature mismatch/);
});
