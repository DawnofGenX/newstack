/** Integration tests: a real listening server on an ephemeral port. */
import assert from "node:assert/strict";
import { after, before, test } from "node:test";

import { createApp } from "../src/app.js";
import { countText } from "../src/counts.js";
import { percentDecode, queryText } from "../src/contract.js";

import type { FastifyInstance } from "fastify";

let app: FastifyInstance;
let base = "";

before(async () => {
  app = createApp();
  const address = await app.listen({ port: 0, host: "127.0.0.1" });
  base = address;
});

after(async () => {
  await app.close();
});

async function call(method: string, path: string, body?: string): Promise<{ status: number; text: string }> {
  const init: RequestInit = { method };
  if (body !== undefined) {
    init.body = body;
    init.headers = { "content-type": "application/json" };
  }
  const response = await fetch(`${base}${path}`, init);
  return { status: response.status, text: await response.text() };
}

test("health answers", async () => {
  const reply = await call("GET", "/health");
  assert.equal(reply.status, 200);
  assert.equal(reply.text, '{"status":"ok"}');
});

test("stats counts a query string", async () => {
  const reply = await call("GET", "/stats?text=a+b%0Ac%0A");
  assert.equal(reply.status, 200);
  assert.equal(reply.text, '{"text":"a b\\nc\\n","lines":2,"words":3,"bytes":6}');
});

test("stats keeps the key order", async () => {
  const reply = await call("GET", "/stats?text=x");
  assert.deepEqual(Object.keys(JSON.parse(reply.text) as object), ["text", "lines", "words", "bytes"]);
});

test("stats accepts a JSON body", async () => {
  const reply = await call("POST", "/stats", '{"text":"héllo wörld\\n"}');
  assert.equal(reply.status, 200);
  assert.equal(reply.text, '{"text":"héllo wörld\\n","lines":1,"words":2,"bytes":14}');
});

test("stats without text is a 422", async () => {
  const reply = await call("POST", "/stats", "{}");
  assert.equal(reply.status, 422);
  assert.equal(reply.text, '{"error":"missing_text"}');
});

test("broken JSON is a 422", async () => {
  const reply = await call("POST", "/stats", '{"text":');
  assert.equal(reply.status, 422);
  assert.equal(reply.text, '{"error":"invalid_json"}');
});

test("a numeric text is a 422", async () => {
  const reply = await call("POST", "/stats", '{"text":7}');
  assert.equal(reply.status, 422);
  assert.equal(reply.text, '{"error":"invalid_json"}');
});

test("wrong method is a 405", async () => {
  const reply = await call("DELETE", "/health");
  assert.equal(reply.status, 405);
});

test("unknown path is a 404 with detail", async () => {
  const reply = await call("GET", "/nope?x=1");
  assert.equal(reply.status, 404);
  assert.equal(reply.text, '{"error":"not_found","detail":"no route for GET /nope"}');
});

test("counting is byte based", () => {
  assert.deepEqual(countText("héllo wörld\n"), { lines: 1, words: 2, bytes: 14 });
});

test("percent decoding treats + as space", () => {
  assert.equal(percentDecode("a+b"), "a b");
  assert.equal(percentDecode("caf%C3%A9"), "café");
});

test("the first query value wins", () => {
  assert.equal(queryText("/stats?text=one&text=two"), "one");
});
