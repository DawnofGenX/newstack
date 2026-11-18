import test from "node:test";
import assert from "node:assert/strict";

import { getPath, parseScalar, parseYaml, stringifyYaml, YamlError } from "../src/yaml.js";

test("parses nested mappings", () => {
  const doc = parseYaml("server:\n  host: localhost\n  port: 8080\nname: demo\n");
  assert.deepEqual(doc, { server: { host: "localhost", port: 8080 }, name: "demo" });
});

test("parses sequences of scalars", () => {
  assert.deepEqual(parseYaml("tags:\n  - a\n  - b\n"), { tags: ["a", "b"] });
});

test("parses sequences of maps", () => {
  const doc = parseYaml("upstreams:\n  - name: one\n    port: 9001\n  - name: two\n    port: 9002\n");
  assert.deepEqual(doc.upstreams, [
    { name: "one", port: 9001 },
    { name: "two", port: 9002 },
  ]);
});

test("parses flow collections", () => {
  const doc = parseYaml("ports: [80, 443]\nnested: {a: 1, b: [2, 3]}\n");
  assert.deepEqual(doc, { ports: [80, 443], nested: { a: 1, b: [2, 3] } });
});

test("understands scalars", () => {
  assert.equal(parseScalar("null"), null);
  assert.equal(parseScalar("~"), null);
  assert.equal(parseScalar("true"), true);
  assert.equal(parseScalar("-12.5"), -12.5);
  assert.equal(parseScalar("'it''s'"), "it's");
  assert.equal(parseScalar('"a\\tb"'), "a\tb");
  assert.equal(parseScalar("plain text"), "plain text");
});

test("comments are stripped outside quotes", () => {
  const doc = parseYaml("a: 1 # trailing\nb: 'x # kept'\nc: a#b\n");
  assert.deepEqual(doc, { a: 1, b: "x # kept", c: "a#b" });
});

test("empty values become null", () => {
  assert.deepEqual(parseYaml("a:\nb: 1\n"), { a: null, b: 1 });
});

test("duplicate keys are rejected", () => {
  assert.throws(() => parseYaml("a: 1\na: 2\n"), (error) => {
    assert.ok(error instanceof YamlError);
    assert.match(error.message, /line 2: duplicate key a/);
    return true;
  });
});

test("a tab indent is rejected with its line", () => {
  assert.throws(() => parseYaml("a:\n\tb: 1\n"), /line 2: tabs are not allowed/);
});

test("a line without a colon is rejected", () => {
  assert.throws(() => parseYaml("a: 1\njust text\n"), /line 2: expected key: value/);
});

test("an unterminated quote is rejected", () => {
  assert.throws(() => parseYaml('a: "open\n'), /unterminated quoted scalar/);
});

test("block scalars are refused by name", () => {
  assert.throws(() => parseYaml("a: |\n  text\n"), /block scalars/);
});

test("stringifyYaml round trips a document", () => {
  const doc = { name: "demo", server: { host: "localhost", port: 8080 }, tags: ["a", "b"] };
  assert.deepEqual(parseYaml(stringifyYaml(doc)), doc);
});

test("stringifyYaml quotes what needs it", () => {
  const text = stringifyYaml({ a: "", b: "1n", c: "x: y", d: "plain" });
  assert.match(text, /a: ""/);
  assert.match(text, /b: "1n"/);
  assert.match(text, /c: "x: y"/);
  assert.match(text, /d: plain/);
});

test("stringifyYaml prints empty collections inline", () => {
  assert.equal(stringifyYaml({ a: [], b: {} }), "a: []\nb: {}");
});

test("stringifyYaml nests sequences of maps", () => {
  const text = stringifyYaml({ items: [{ a: 1 }] });
  assert.deepEqual(parseYaml(text), { items: [{ a: 1 }] });
});

test("getPath walks maps and indexes", () => {
  const doc = parseYaml("server:\n  hosts:\n    - one\n    - two\n");
  assert.equal(getPath(doc, "server.hosts[1]"), "two");
  assert.equal(getPath(doc, "server.port"), undefined);
});
