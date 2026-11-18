import { test } from "node:test";
import assert from "node:assert/strict";
import { applyPatch, diff } from "../src/patch.js";

test("add", () => {
  const out = applyPatch({ foo: 1 }, [{ op: "add", path: "/bar", value: 2 }]);
  assert.deepEqual(out, { foo: 1, bar: 2 });
});

test("remove", () => {
  const out = applyPatch({ foo: 1, bar: 2 }, [{ op: "remove", path: "/bar" }]);
  assert.deepEqual(out, { foo: 1 });
});

test("replace", () => {
  const out = applyPatch({ foo: 1 }, [{ op: "replace", path: "/foo", value: 9 }]);
  assert.deepEqual(out, { foo: 9 });
});

test("move", () => {
  const out = applyPatch({ a: 1 }, [{ op: "move", from: "/a", path: "/b" }]);
  assert.deepEqual(out, { b: 1 });
});

test("copy", () => {
  const out = applyPatch({ a: 1 }, [{ op: "copy", from: "/a", path: "/b" }]);
  assert.deepEqual(out, { a: 1, b: 1 });
});

test("test op passes", () => {
  const out = applyPatch({ a: 1 }, [{ op: "test", path: "/a", value: 1 }, { op: "replace", path: "/a", value: 2 }]);
  assert.deepEqual(out, { a: 2 });
});

test("test op fails", () => {
  assert.throws(() => applyPatch({ a: 1 }, [{ op: "test", path: "/a", value: 2 }]));
});

test("add to array index", () => {
  const out = applyPatch({ arr: [1, 2] }, [{ op: "add", path: "/arr/1", value: 9 }]);
  assert.deepEqual(out, { arr: [1, 9, 2] });
});

test("remove array element", () => {
  const out = applyPatch({ arr: [1, 2, 3] }, [{ op: "remove", path: "/arr/1" }]);
  assert.deepEqual(out, { arr: [1, 3] });
});

test("diff produces ops", () => {
  const ops = diff({ a: 1, b: 2 }, { a: 1, b: 3, c: 4 });
  assert.ok(ops.some((o) => o.op === "replace" && o.path === "/b"));
  assert.ok(ops.some((o) => o.op === "add" && o.path === "/c"));
});

test("nested replace", () => {
  const out = applyPatch({ x: { y: 1 } }, [{ op: "replace", path: "/x/y", value: 5 }]);
  assert.deepEqual(out, { x: { y: 5 } });
});