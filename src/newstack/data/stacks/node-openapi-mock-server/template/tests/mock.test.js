import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer as cs } from "../src/server.js";
import { loadSpec as ls } from "../src/openapi.js";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

function makeServer(spec) {
  const dir = mkdtempSync(join(tmpdir(), "oas-"));
  const p = join(dir, "openapi.json");
  writeFileSync(p, JSON.stringify(spec));
  const s = cs({ spec: ls(p) });
  return new Promise((resolve) => {
    s.listen(0, "127.0.0.1", () => resolve({ server: s, port: s.address().port }));
  });
}

const SPEC = {
  openapi: "3.0.0",
  info: { title: "t", version: "1" },
  paths: {
    "/health": {
      get: { responses: { "200": { content: { "application/json": { example: { status: "ok" } } } } } }
    },
    "/items/{id}": {
      parameters: [{ name: "id", in: "path", required: true, schema: { type: "string" } }],
      get: { responses: { "200": { content: { "application/json": { schema: { type: "object", properties: { id: { type: "string" }, name: { type: "string" } } } } } } } },
      delete: { responses: { "204": { description: "no content" } } }
    },
    "/search": {
      get: {
        parameters: [{ name: "q", in: "query", required: true, schema: { type: "string" } }],
        responses: { "200": { content: { "application/json": { example: { q: "x" } } } } }
      }
    }
  }
};

test("example response", async () => {
  const { server, port } = await makeServer(SPEC);
  const res = await fetch(`http://127.0.0.1:${port}/health`);
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { status: "ok" });
  server.close();
});

test("schema-shaped default", async () => {
  const { server, port } = await makeServer(SPEC);
  const res = await fetch(`http://127.0.0.1:${port}/items/42`);
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { id: "string", name: "string" });
  server.close();
});

test("404 unknown path lists paths", async () => {
  const { server, port } = await makeServer(SPEC);
  const res = await fetch(`http://127.0.0.1:${port}/nope`);
  assert.equal(res.status, 404);
  const body = await res.json();
  assert.equal(body.error, "not_found");
  assert.ok(Array.isArray(body.paths));
  server.close();
});

test("405 wrong method", async () => {
  const { server, port } = await makeServer(SPEC);
  const res = await fetch(`http://127.0.0.1:${port}/health`, { method: "POST" });
  assert.equal(res.status, 405);
  const body = await res.json();
  assert.equal(body.error, "method_not_allowed");
  assert.ok(body.allow.includes("GET"));
  server.close();
});

test("required query param", async () => {
  const { server, port } = await makeServer(SPEC);
  const res = await fetch(`http://127.0.0.1:${port}/search`);
  assert.equal(res.status, 400);
  const body = await res.json();
  assert.equal(body.error, "validation_error");
  server.close();
});

test("required query param ok", async () => {
  const { server, port } = await makeServer(SPEC);
  const res = await fetch(`http://127.0.0.1:${port}/search?q=hi`);
  assert.equal(res.status, 200);
  server.close();
});