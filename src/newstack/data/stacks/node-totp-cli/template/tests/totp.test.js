import { test } from "node:test";
import assert from "node:assert/strict";
import { totp, verify, base32Decode } from "../src/totp.js";

const SHA1_SECRET = "12345678901234567890";
const SHA256_SECRET = "12345678901234567890123456789012";
const SHA512_SECRET = "1234567890123456789012345678901234567890123456789012345678901234";

const SHA1_VECTORS = [
  [59, "94287082"],
  [1111111109, "07081804"],
  [1111111111, "14050471"],
  [1234567890, "89005924"],
  [2000000000, "69279037"],
  [20000000000, "65353130"],
];

test("RFC6238 SHA1 vectors", () => {
  for (const [t, code] of SHA1_VECTORS) {
    assert.equal(totp(SHA1_SECRET, t, { digits: 8, algo: "sha1" }), code, `t=${t}`);
  }
});

const SHA256_VECTORS = [
  [59, "46119246"],
  [1111111109, "68084774"],
  [1111111111, "67062674"],
  [1234567890, "91819424"],
  [2000000000, "90698825"],
  [20000000000, "77737706"],
];

test("RFC6238 SHA256 vectors", () => {
  for (const [t, code] of SHA256_VECTORS) {
    assert.equal(totp(SHA256_SECRET, t, { digits: 8, algo: "sha256" }), code, `t=${t}`);
  }
});

const SHA512_VECTORS = [
  [59, "90693936"],
  [1111111109, "25091201"],
  [1111111111, "99943326"],
  [1234567890, "93441116"],
  [2000000000, "38618901"],
  [20000000000, "47863826"],
];

test("RFC6238 SHA512 vectors", () => {
  for (const [t, code] of SHA512_VECTORS) {
    assert.equal(totp(SHA512_SECRET, t, { digits: 8, algo: "sha512" }), code, `t=${t}`);
  }
});

test("verify accepts correct code", () => {
  const code = totp(SHA1_SECRET, 59, { digits: 8, algo: "sha1" });
  assert.equal(verify(SHA1_SECRET, code, 59, { digits: 8, algo: "sha1" }), true);
});

test("verify rejects wrong code", () => {
  assert.equal(verify(SHA1_SECRET, "00000000", 59, { digits: 8, algo: "sha1" }), false);
});

test("base32 decode", () => {
  assert.equal(base32Decode("JBSWY3DPEE======").toString("utf8"), "Hello!");
});