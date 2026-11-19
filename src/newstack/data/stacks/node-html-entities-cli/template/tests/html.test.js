import { test } from "node:test";
import assert from "node:assert/strict";
import { encodeEntities, decodeEntities } from "../src/html.js";

test("encode basic", () => {
  assert.equal(encodeEntities(`<b>"hi"&'x'</b>`), "&lt;b&gt;&quot;hi&quot;&amp;&#39;x&#39;&lt;/b&gt;");
});

test("decode named", () => {
  assert.equal(decodeEntities("&lt;p&gt;Tom &amp; Jerry&lt;/p&gt;"), "<p>Tom & Jerry</p>");
});

test("decode numeric", () => {
  assert.equal(decodeEntities("&#65;&#x42;"), "AB");
});

test("roundtrip", () => {
  const s = `<script>alert("x&y")</script>`;
  assert.equal(decodeEntities(encodeEntities(s)), s);
});