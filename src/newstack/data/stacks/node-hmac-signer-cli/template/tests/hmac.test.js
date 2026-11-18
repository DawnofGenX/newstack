import { test } from "node:test";
import assert from "node:assert/strict";
import { computeSignature, verifySignature } from "../src/hmac.js";

test("sign prints v1= prefix", () => {
  const sig = computeSignature("secret", "hello", 1700000000);
  assert.match(sig, /^v1=[0-9a-f]{64}$/);
});

test("verify accepts valid signature", () => {
  const sig = computeSignature("secret", "hello", 1700000000);
  assert.equal(
    verifySignature("secret", "hello", sig, 1700000000, 1000000000),
    true,
  );
});

test("verify rejects tampered payload", () => {
  const sig = computeSignature("secret", "hello", 1700000000);
  assert.equal(
    verifySignature("secret", "tampered", sig, 1700000000, 1000000000),
    false,
  );
});

test("verify rejects wrong signature", () => {
  assert.equal(
    verifySignature("secret", "hello", "v1=" + "0".repeat(64), 1700000000, 1000000000),
    false,
  );
});

test("verify rejects expired timestamp", () => {
  const sig = computeSignature("secret", "hello", 1700000000);
  assert.equal(verifySignature("secret", "hello", sig, 1700000000, 300), false);
});
