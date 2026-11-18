import { test } from "node:test";
import assert from "node:assert/strict";
import { render, escapeHtml } from "../src/renderer.js";

test("variable with escaping", () => {
  assert.equal(render("Hi {{!name}}", { name: "<b>x</b>" }), "Hi &lt;b&gt;x&lt;/b&gt;");
});

test("section true", () => {
  assert.equal(render("{{#show}}yes{{/show}}", { show: true }), "yes");
});

test("inverted", () => {
  assert.equal(render("{{^items}}none{{/items}}", { items: [] }), "none");
  assert.equal(render("{{^items}}none{{/items}}", { items: [1] }), "");
});

test("section array", () => {
  assert.equal(render("{{#items}}{{.}}{{/items}}", { items: [1, 2] }), "12");
});

test("partial", () => {
  assert.equal(render("{{> p}}", {}, { p: "PARTIAL" }), "PARTIAL");
});
