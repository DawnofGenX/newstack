import assert from "node:assert/strict";
import { test } from "node:test";
import { library } from "../src/demo.js";
import { cacheControl, representation } from "../src/resource.js";
import { respond } from "../src/server.js";
import { strongTag, weakTag } from "../src/etag.js";
import { requestOnce } from "../src/cache.js";
import { createServer } from "../src/server.js";

const doc = library().get("/profile");
const varied = library().get("/report");
if (doc === undefined || varied === undefined) {
  throw new Error("fixtures are missing");
}

test("a plain GET answers 200 with a tag and a length", () => {
  const sent = respond(doc, { method: "GET", accept: "*/*" });
  assert.equal(sent.status, 200);
  assert.equal(sent.headers["content-length"], String(Buffer.byteLength(sent.body)));
  assert.match(sent.headers["etag"] ?? "", /^"[0-9a-f]{16}"$/);
});

test("a matching If-None-Match answers 304 with no body", () => {
  const plain = respond(doc, { method: "GET", accept: "*/*" });
  const sent = respond(doc, { method: "GET", accept: "*/*", ifNoneMatch: plain.headers["etag"] ?? "" });
  assert.equal(sent.status, 304);
  assert.equal(sent.body, "");
  assert.equal(sent.headers["etag"], plain.headers["etag"]);
  assert.equal(sent.headers["content-length"], undefined);
});

test("If-Match does not accept a weak tag", () => {
  assert.equal(respond(doc, { method: "PUT", accept: "*/*", ifMatch: weakTag(doc.body) }).status, 412);
  assert.equal(respond(doc, { method: "PUT", accept: "*/*", ifMatch: strongTag(doc.body) }).status, 204);
  assert.equal(respond(doc, { method: "PUT", accept: "*/*" }).status, 428);
});

test("If-None-Match wins over If-Modified-Since", () => {
  const old = "Thu, 01 Jan 1970 00:00:00 GMT";
  assert.equal(respond(doc, { method: "GET", accept: "*/*", ifModifiedSince: old }).status, 200);
  const both = respond(doc, {
    method: "GET",
    accept: "*/*",
    ifNoneMatch: strongTag(doc.body),
    ifModifiedSince: old,
  });
  assert.equal(both.status, 304);
  assert.equal(respond(doc, { method: "GET", accept: "*/*", ifModifiedSince: new Date(doc.changedAt).toUTCString() }).status, 304);
});

test("Vary is announced only where it applies", () => {
  assert.equal(respond(doc, { method: "GET", accept: "*/*" }).headers["vary"], undefined);
  const json = respond(varied, { method: "GET", accept: "application/json" });
  const text = respond(varied, { method: "GET", accept: "text/plain" });
  assert.equal(json.headers["vary"], "accept");
  assert.notEqual(json.body, text.body);
  assert.equal(representation(doc, "text/plain"), doc.body);
});

test("no-store is not a lifetime", () => {
  const privateDoc = library().get("/private");
  assert.ok(privateDoc);
  assert.equal(cacheControl(privateDoc), "no-store");
});

test("a live server answers 304 for a matching tag", async () => {
  const handle = await createServer(library());
  try {
    const origin = `http://127.0.0.1:${handle.port}`;
    const first = await requestOnce(origin, "/profile", "application/json");
    const tag = first.headers["etag"];
    assert.ok(typeof tag === "string");
    const second = await requestOnce(origin, "/profile", "application/json", { "if-none-match": tag });
    assert.equal(second.status, 304);
    assert.equal(second.bytes, 0);
    const missing = await requestOnce(origin, "/nope", "application/json");
    assert.equal(missing.status, 404);
  } finally {
    await handle.close();
  }
});
