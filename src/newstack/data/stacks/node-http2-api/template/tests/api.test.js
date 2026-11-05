import assert from "node:assert/strict";
import http2 from "node:http2";
import { after, before, describe, it } from "node:test";

import { countText } from "../src/counts.js";
import { createServer, listen, stop } from "../src/server.js";

let client;
let server;

function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const stream = client.request({ ":method": method, ":path": path });
    let status = 0;
    let type = "";
    let payload = "";
    stream.on("response", (headers) => {
      status = headers[":status"];
      type = headers["content-type"];
    });
    stream.setEncoding("utf8");
    stream.on("data", (chunk) => {
      payload += chunk;
    });
    stream.on("end", () => resolve({ status, type, body: payload }));
    stream.on("error", reject);
    stream.end(body);
  });
}

before(async () => {
  const listening = createServer();
  server = listening.server;
  const { port } = await listen(server, "127.0.0.1", 0);
  client = http2.connect(`http://127.0.0.1:${port}`);
});

after(async () => {
  client.close();
  await stop(server);
});

describe("counts", () => {
  it("counts bytes, not characters", () => {
    assert.deepEqual(countText("h\u00e9llo w\u00f6rld\n"), { lines: 1, words: 2, bytes: 14 });
  });

  it("treats a carriage return as a separator", () => {
    assert.deepEqual(countText("a\rb"), { lines: 0, words: 2, bytes: 3 });
  });
});

describe("h2c app", () => {
  it("answers /health over HTTP/2", async () => {
    const answer = await request("GET", "/health");
    assert.equal(answer.status, 200);
    assert.equal(answer.type, "application/json; charset=utf-8");
    assert.equal(JSON.parse(answer.body).protocol, "h2");
  });

  it("counts text from the query", async () => {
    const answer = await request("GET", "/stats?text=a%20b%0A");
    assert.deepEqual(JSON.parse(answer.body), { text: "a b\n", lines: 1, words: 2, bytes: 4 });
  });

  it("keeps a body byte count honest for utf-8", async () => {
    const body = JSON.stringify({ text: "h\u00e9llo w\u00f6rld\n" });
    const answer = await request("POST", "/stats", body);
    assert.equal(JSON.parse(answer.body).bytes, 14);
  });

  it("separates a missing text from an invalid one", async () => {
    const missing = await request("POST", "/stats", "{}");
    const invalid = await request("POST", "/stats", '{"text":42}');
    assert.equal(JSON.parse(missing.body).error, "missing_text");
    assert.equal(JSON.parse(invalid.body).error, "invalid_json");
  });

  it("owns the 404 and 405 bodies", async () => {
    const gone = await request("GET", "/nope");
    const wrong = await request("PUT", "/health");
    assert.equal(gone.status, 404);
    assert.equal(JSON.parse(gone.body).detail, "no route for GET /nope");
    assert.equal(wrong.status, 405);
    assert.equal(JSON.parse(wrong.body).error, "method_not_allowed");
  });

  it("serves three streams at once", async () => {
    const answers = await Promise.all([
      request("GET", "/stats?text=a"),
      request("GET", "/stats?text=b"),
      request("GET", "/stats?text=c"),
    ]);
    assert.deepEqual(answers.map((one) => JSON.parse(one.body).text), ["a", "b", "c"]);
  });
});
