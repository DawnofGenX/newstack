import test from "node:test";
import assert from "node:assert/strict";
import { run } from "../src/cli.js";

const drive = (lines, options = {}) => {
  const out = [];
  const result = run(lines, { capacity: 4, ttlMs: 0, out: (line) => out.push(line), ...options });
  return { ...result, out };
};

test("set then get round-trips a json value", () => {
  const { out, code } = drive(["SET a 1", "GET a"]);
  assert.equal(code, 0);
  assert.deepEqual(out, ["OK", "1"]);
});

test("a bare word value is kept as a string", () => {
  assert.deepEqual(drive(["SET mode prod", "GET mode"]).out, ["OK", '"prod"']);
});

test("a missing key prints (nil)", () => {
  assert.deepEqual(drive(["GET missing"]).out, ["(nil)"]);
});

test("del reports whether the key existed", () => {
  assert.deepEqual(drive(["SET a 1", "DEL a", "DEL a"]).out, ["OK", "1", "0"]);
});

test("advance moves the virtual clock and expires entries", () => {
  const { out } = drive(["SET a 1 100", "ADVANCE 100", "GET a", "STATS"]);
  assert.deepEqual(out, ["OK", "now=100", "(nil)", "hits=0 misses=1 evictions=0 expirations=1 entries=0"]);
});

test("keys are listed least recently used first", () => {
  const { out } = drive(["SET a 1", "SET b 2", "GET a", "KEYS"]);
  assert.equal(out.at(-1), "b a");
});

test("a comment line is ignored", () => {
  assert.deepEqual(drive(["# nothing here", "GET a"]).out, ["(nil)"]);
});

test("an unknown command stops with an error", () => {
  const { code } = drive(["FLUSH"]);
  assert.equal(code, 1);
});

test("set without a value is a command error", () => {
  assert.equal(drive(["SET lonely"]).code, 1);
});
