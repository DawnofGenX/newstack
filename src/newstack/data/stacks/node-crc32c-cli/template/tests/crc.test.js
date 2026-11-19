import { test } from "node:test";
import assert from "node:assert/strict";
import { crc32c } from "../src/crc.js";

test("known vector", () => {
  assert.equal(crc32c("123456789"), 0xe3069283);
});

test("empty", () => {
  assert.equal(crc32c(""), 0x00000000);
});

test("deterministic", () => {
  assert.equal(crc32c("hello world"), crc32c("hello world"));
});