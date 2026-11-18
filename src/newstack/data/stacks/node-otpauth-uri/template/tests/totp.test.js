import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { totp, hotp, otpauthUri, parseOtpauthUri, base32Decode, base32Encode } from "../src/totp.js";

const RFC_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ";

test("base32 roundtrip", () => {
  const raw = Buffer.from("12345678901234567890", "ascii");
  assert.equal(base32Encode(raw), RFC_SECRET);
  assert.deepEqual(base32Decode(RFC_SECRET), raw);
});

test("base32 rejects non alphabet characters", () => {
  assert.throws(() => base32Decode("not-base32!"), /invalid base32/);
});

test("hotp matches RFC 4226 vectors", () => {
  assert.equal(hotp(RFC_SECRET, 0), "755224");
  assert.equal(hotp(RFC_SECRET, 1), "287082");
  assert.equal(hotp(RFC_SECRET, 8), "399871");
});

test("totp matches RFC 6238 vector at t=59s", () => {
  assert.equal(totp(RFC_SECRET, { time: 59_000, digits: 8 }), "94287082");
  assert.equal(totp(RFC_SECRET, { time: 59_000, digits: 6 }), "287082");
});

test("totp advances every period", () => {
  const a = totp(RFC_SECRET, { time: 0 });
  const b = totp(RFC_SECRET, { time: 30_000 });
  assert.notEqual(a, b);
  assert.equal(totp(RFC_SECRET, { time: 29_000 }), a);
});

test("otpauth uri roundtrip", () => {
  const uri = otpauthUri({ secret: RFC_SECRET, issuer: "Acme", account: "alice@example.com" });
  assert.match(uri, /^otpauth:\/\/totp\/Acme:alice%40example\.com\?/);
  const parsed = parseOtpauthUri(uri);
  assert.deepEqual(
    { secret: parsed.secret, issuer: parsed.issuer, account: parsed.account, digits: parsed.digits, period: parsed.period },
    { secret: RFC_SECRET, issuer: "Acme", account: "alice@example.com", digits: 6, period: 30 }
  );
});

test("parse rejects foreign uris", () => {
  assert.throws(() => parseOtpauthUri("https://example.com/"), /not an otpauth uri/);
  assert.throws(() => parseOtpauthUri("otpauth://hotp/x?secret=AA"), /unsupported type/);
});

test("cli prints uri then parses it back", () => {
  const uriRes = spawnSync(process.execPath, ["src/cli.js", "uri", "--secret", RFC_SECRET, "--issuer", "Acme", "--account", "alice@example.com"], { encoding: "utf8" });
  assert.equal(uriRes.status, 0, uriRes.stderr);
  const uri = uriRes.stdout.trim();
  assert.match(uri, /^otpauth:\/\//);
  const parseRes = spawnSync(process.execPath, ["src/cli.js", "parse", uri], { encoding: "utf8" });
  assert.equal(parseRes.status, 0, parseRes.stderr);
  assert.equal(JSON.parse(parseRes.stdout).secret, RFC_SECRET);
});

test("cli code matches library and rejects bad usage", () => {
  const res = spawnSync(process.execPath, ["src/cli.js", "code", "--secret", RFC_SECRET, "--counter", "1"], { encoding: "utf8" });
  assert.equal(res.status, 0, res.stderr);
  assert.equal(res.stdout.trim(), "287082");
  const bad = spawnSync(process.execPath, ["src/cli.js", "nope"], { encoding: "utf8" });
  assert.equal(bad.status, 2);
});
