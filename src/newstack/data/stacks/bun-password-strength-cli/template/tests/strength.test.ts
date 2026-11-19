import { test, expect } from "bun:test";
import { scorePassword } from "../src/strength.ts";

test("weak password", () => {
  const r = scorePassword("password");
  expect(r.score).toBeLessThanOrEqual(1);
});

test("strong password", () => {
  const r = scorePassword("Tr0ub4dor&3");
  expect(r.score).toBeGreaterThanOrEqual(3);
});

test("empty", () => {
  const r = scorePassword("");
  expect(r.score).toBe(0);
  expect(r.label).toBe("very weak");
});

test("pinned score", () => {
  const r = scorePassword("Abcdefgh1!xy");
  expect(r.score).toBe(4);
});