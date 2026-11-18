import test from "node:test";
import assert from "node:assert/strict";
import { validate, isValid, typeOf } from "../src/schema.js";

const messages = (value, schema) => validate(value, schema).map((entry) => `${entry.path}: ${entry.message}`);

test("a matching document has no problems", () => {
  assert.deepEqual(messages({ a: 1 }, { type: "object", properties: { a: { type: "integer" } } }), []);
});

test("a wrong type reports the path and both types", () => {
  assert.deepEqual(messages({ a: "x" }, { properties: { a: { type: "integer" } } }), [
    "$.a: expected integer, got string",
  ]);
});

test("integer is reported separately from number", () => {
  assert.equal(typeOf(1), "integer");
  assert.equal(typeOf(1.5), "number");
  assert.equal(typeOf(null), "null");
  assert.equal(isValid(1.5, { type: "number" }), true);
  assert.equal(isValid(1.5, { type: "integer" }), false);
});

test("every required key is reported", () => {
  assert.deepEqual(messages({}, { type: "object", required: ["a", "b"] }), [
    "$.a: is required",
    "$.b: is required",
  ]);
});

test("a nested array item keeps its index in the path", () => {
  assert.deepEqual(messages({ tags: ["ok", 3] }, {
    properties: { tags: { type: "array", items: { type: "string" } } },
  }), ["$.tags[1]: expected string, got integer"]);
});

test("additionalProperties false names each extra key", () => {
  assert.deepEqual(messages({ a: 1, b: 2 }, {
    type: "object",
    properties: { a: { type: "integer" } },
    additionalProperties: false,
  }), ["$.b: is not an allowed property"]);
});

test("a schema-valued additionalProperties validates the extras", () => {
  assert.deepEqual(messages({ a: 1, b: "no" }, {
    properties: { a: { type: "integer" } },
    additionalProperties: { type: "integer" },
  }), ["$.b: expected integer, got string"]);
});

test("bounds are inclusive unless they are exclusive", () => {
  assert.equal(isValid(1, { minimum: 1, maximum: 2 }), true);
  assert.equal(isValid(1, { exclusiveMinimum: 1 }), false);
  assert.equal(isValid(4, { multipleOf: 2 }), true);
  assert.equal(isValid(5, { multipleOf: 2 }), false);
});

test("string keywords are enforced", () => {
  assert.deepEqual(messages("ab", { minLength: 3 }), ["$: must be at least 3 characters"]);
  assert.deepEqual(messages("abc", { pattern: "^[0-9]+$" }), ["$: does not match pattern ^[0-9]+$"]);
  assert.deepEqual(messages("nope", { format: "email" }), ["$: does not match format email"]);
});

test("date format rejects a plausible but impossible date", () => {
  assert.equal(isValid("2024-02-29", { format: "date" }), true);
  assert.equal(isValid("2024-13-01", { format: "date" }), false);
});

test("uniqueItems compares by deep value", () => {
  assert.equal(isValid([{ a: 1 }, { a: 1 }], { uniqueItems: true }), false);
  assert.equal(isValid([{ a: 1 }, { a: 2 }], { uniqueItems: true }), true);
});

test("enum and const compare by deep value", () => {
  assert.equal(isValid("b", { enum: ["a", "b"] }), true);
  assert.deepEqual(messages("c", { enum: ["a", "b"] }), ['$: must be one of "a", "b"']);
  assert.equal(isValid({ a: 1 }, { const: { a: 1 } }), true);
});

test("oneOf demands exactly one match", () => {
  const schema = { oneOf: [{ type: "integer" }, { type: "number" }] };
  assert.deepEqual(messages(1, schema), ["$: must match exactly one oneOf branch, matched 2"]);
  assert.equal(isValid("x", { oneOf: [{ type: "string" }, { type: "null" }] }), true);
});

test("anyOf demands at least one match", () => {
  assert.equal(isValid("x", { anyOf: [{ type: "string" }, { type: "null" }] }), true);
  assert.equal(isValid(1, { anyOf: [{ type: "string" }, { type: "null" }] }), false);
});

test("not inverts the branch", () => {
  assert.equal(isValid("x", { not: { type: "string" } }), false);
  assert.equal(isValid(1, { not: { type: "string" } }), true);
});

test("a false schema rejects everything", () => {
  assert.deepEqual(messages(1, false), ["$: no value is allowed here"]);
});
