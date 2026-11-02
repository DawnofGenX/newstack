import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (name) => readFile(new URL(`../${name}`, import.meta.url), "utf8");

test("index.html is a complete document", async () => {
  const html = await read("index.html");
  assert.match(html, /<!doctype html>/i);
  assert.match(html, /<title>.+<\/title>/);
  assert.match(html, /<main[^>]*>/);
  assert.match(html, /href="styles\.css"/);
  assert.match(html, /src="main\.js"/);
});

test("styles.css styles the hero block", async () => {
  assert.match(await read("styles.css"), /\.hero\s*\{/);
});

test("main.js wires the footer year", async () => {
  assert.match(await read("main.js"), /getElementById\("year"\)/);
});
