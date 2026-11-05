import assert from "node:assert/strict";
import { test } from "node:test";
import { anyMatch, parseList, parseTag, renderTag, strongCompare, strongTag, weakCompare, weakTag } from "../src/etag.js";

test("a strong tag is quoted and a weak one is marked", () => {
  const tag = strongTag("hello");
  assert.match(tag, /^"[0-9a-f]{16}"$/);
  assert.equal(weakTag("hello"), `W/${tag}`);
});

test("parsing rejects anything that is not a quoted tag", () => {
  assert.equal(parseTag("abc"), null);
  assert.equal(parseTag('"unterminated'), null);
  assert.deepEqual(parseTag('W/"x"'), { weak: true, opaque: "x" });
  assert.equal(renderTag(parseTag('"x"') ?? { weak: true, opaque: "" }), '"x"');
});

test("the weak comparison ignores the marker and the strong one does not", () => {
  const strong = parseTag(strongTag("hello"));
  const weak = parseTag(weakTag("hello"));
  assert.ok(strong && weak);
  assert.ok(weakCompare(weak, strong));
  assert.ok(!strongCompare(weak, strong));
  assert.ok(strongCompare(strong, strong));
  assert.ok(!strongCompare(weak, weak));
});

test("If-None-Match is weak and If-Match is strong", () => {
  const tag = strongTag("hello");
  assert.ok(anyMatch(weakTag("hello"), tag, "weak"));
  assert.ok(!anyMatch(weakTag("hello"), tag, "strong"));
  assert.ok(anyMatch(tag, tag, "strong"));
});

test("a list holds tags and a star is not one", () => {
  const list = parseList('"a", W/"b"');
  assert.equal(list.tags.length, 2);
  assert.equal(list.any, false);
  assert.equal(parseList("*").any, true);
  assert.equal(parseList("").tags.length, 0);
  assert.ok(anyMatch("*", strongTag("x"), "strong"));
});
