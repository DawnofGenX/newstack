import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { parse } from "yaml";

import { createHttpServer } from "../src/server.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
// `npm test` bundles first, so this is the artifact a client generator would consume —
// validating against the source document would let a broken $ref survive.
const spec = parse(await readFile(join(root, "dist", "openapi.yaml"), "utf8"));

const ajv = new Ajv2020({ strict: false, allErrors: true });
addFormats(ajv);
ajv.addSchema(spec, "spec");

function check(schema, value) {
  // The bundled document keeps internal refs (`#/components/...`); compiled on its own,
  // such a ref resolves against that schema as root, so re-anchor it at `spec`.
  const anchored = JSON.parse(JSON.stringify(schema).replaceAll('"#/', '"spec#/'));
  const validate = ajv.compile(anchored);
  const ok = validate(value);
  assert.ok(ok, `response does not match the document: ${ajv.errorsText(validate.errors)}`);
}

function schemaFor(path, method, status) {
  return spec.paths[path][method].responses[status].content["application/json"].schema;
}

let server;
let base;

before(async () => {
  server = createHttpServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => new Promise((resolve) => server.close(resolve)));

test("the document is OpenAPI 3.1 and declares the routes the server serves", () => {
  assert.equal(spec.openapi, "3.1.0");
  assert.deepEqual(Object.keys(spec.paths).sort(), ["/health", "/stats"]);
  for (const [path, item] of Object.entries(spec.paths)) {
    for (const [method, operation] of Object.entries(item)) {
      assert.ok(operation.operationId, `${method} ${path} has no operationId`);
      assert.ok(operation.summary, `${method} ${path} has no summary`);
    }
  }
});

test("every $ref in the document resolves", () => {
  const missing = [];
  const walk = (node, path) => {
    if (node === null || typeof node !== "object") return;
    if (typeof node.$ref === "string" && node.$ref.startsWith("#/")) {
      const target = node.$ref
        .slice(2)
        .split("/")
        .reduce((cursor, key) => cursor?.[key], spec);
      if (target === undefined) missing.push(`${path} -> ${node.$ref}`);
    }
    for (const [key, value] of Object.entries(node)) walk(value, `${path}/${key}`);
  };
  walk(spec, "");
  assert.deepEqual(missing, []);
});

test("GET /health matches the documented schema", async () => {
  const response = await fetch(`${base}/health`);
  assert.equal(response.status, 200);
  const body = await response.json();
  check(schemaFor("/health", "get", 200), body);
  assert.deepEqual(body, { status: "ok" });
});

test("GET /stats counts the text it is given", async () => {
  const response = await fetch(`${base}/stats?text=hello%20world%0A`);
  assert.equal(response.status, 200);
  const body = await response.json();
  check(schemaFor("/stats", "get", 200), body);
  assert.deepEqual(body, { text: "hello world\n", lines: 1, words: 2, bytes: 12 });
});

test("GET /stats without text is the documented 422", async () => {
  const response = await fetch(`${base}/stats`);
  assert.equal(response.status, 422);
  const body = await response.json();
  check(schemaFor("/stats", "get", 422), body);
  assert.equal(body.error, "missing_text");
});

test("POST /stats accepts a JSON body and counts it exactly as sent", async () => {
  const response = await fetch(`${base}/stats`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text: "  padded  \n" }),
  });
  assert.equal(response.status, 200);
  const body = await response.json();
  check(schemaFor("/stats", "post", 200), body);
  assert.deepEqual(body, { text: "  padded  \n", lines: 1, words: 1, bytes: 11 });
});

test("POST /stats rejects a body without a string text", async () => {
  for (const body of [JSON.stringify({}), JSON.stringify({ text: 42 }), "not json"]) {
    const response = await fetch(`${base}/stats`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
    });
    assert.equal(response.status, 422);
    check(schemaFor("/stats", "post", 422), await response.json());
  }
});

test("an undocumented route is still a JSON 404", async () => {
  const response = await fetch(`${base}/nope`);
  assert.equal(response.status, 404);
  assert.equal(response.headers.get("content-type"), "application/json; charset=utf-8");
  const body = await response.json();
  check(spec.components.schemas.Error, body);
  assert.equal(body.error, "not_found");
});
