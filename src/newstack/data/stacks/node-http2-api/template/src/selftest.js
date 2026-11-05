import http2 from "node:http2";

import { countText } from "./counts.js";
import { queryText, readTextMember } from "./json.js";
import { createServer, listen, stop } from "./server.js";

let failures = 0;
let checks = 0;

function check(name, ok, detail) {
  checks += 1;
  if (ok) {
    console.log(`ok  ${name}`);
  } else {
    failures += 1;
    console.log(`FAIL ${name}${detail === undefined ? "" : `: ${detail}`}`);
  }
}

function same(name, got, want) {
  const a = JSON.stringify(got);
  const b = JSON.stringify(want);
  check(name, a === b, `want ${b}, got ${a}`);
}

function request(client, method, path, body) {
  return new Promise((resolve, reject) => {
    const stream = client.request({ ":method": method, ":path": path });
    let status = 0;
    let type = "";
    let payload = "";
    stream.on("response", (headers) => {
      status = headers[":status"];
      type = String(headers["content-type"] || "");
    });
    stream.setEncoding("utf8");
    stream.on("data", (chunk) => {
      payload += chunk;
    });
    stream.on("end", () => resolve({ status, type, body: payload }));
    stream.on("error", reject);
    stream.end(body === undefined ? undefined : body);
  });
}

export async function runSelftest() {
  same("empty text", countText(""), { lines: 0, words: 0, bytes: 0 });
  same("one line", countText("a b\n"), { lines: 1, words: 2, bytes: 4 });
  same("utf8 bytes", countText("h\u00e9llo w\u00f6rld\n"), { lines: 1, words: 2, bytes: 14 });
  same("two lines", countText("a b\nc\n"), { lines: 2, words: 3, bytes: 6 });
  same("cr is a separator", countText("a\rb"), { lines: 0, words: 2, bytes: 3 });
  same("query text", queryText("?text=hi"), "hi");
  same("query percent", queryText("?text=a%20b"), "a b");
  same("query first wins", queryText("?text=one&text=two"), "one");
  same("query absent", queryText("?other=1"), null);
  same("query empty value", queryText("?text="), "");
  same("member text", readTextMember('{"text":"hi"}'), { kind: "text", text: "hi" });
  same("member missing", readTextMember("{}"), { kind: "missing" });
  same("member number", readTextMember('{"text":42}'), { kind: "invalid" });
  same("member broken", readTextMember("{"), { kind: "invalid" });
  same("member array", readTextMember("[]"), { kind: "invalid" });

  const { server } = createServer();
  const { port } = await listen(server, "127.0.0.1", 0);
  const client = http2.connect(`http://127.0.0.1:${port}`);

  try {
    const health = await request(client, "GET", "/health");
    same("health status", health.status, 200);
    same("health type", health.type, "application/json; charset=utf-8");
    const healthBody = JSON.parse(health.body);
    same("health body", healthBody.status, "ok");
    same("health protocol", healthBody.protocol, "h2");
    check("health counts requests", healthBody.requests === 1, `got ${healthBody.requests}`);

    const get = await request(client, "GET", "/stats?text=a%20b%0A");
    same("get status", get.status, 200);
    same("get body", JSON.parse(get.body), { text: "a b\n", lines: 1, words: 2, bytes: 4 });

    const utf8 = await request(client, "GET", "/stats?text=h%C3%A9llo%20w%C3%B6rld%0A");
    same("utf8 bytes", JSON.parse(utf8.body).bytes, 14);

    const post = await request(client, "POST", "/stats", JSON.stringify({ text: "a b\nc\n" }));
    same("post body", JSON.parse(post.body), { text: "a b\nc\n", lines: 2, words: 3, bytes: 6 });

    const empty = await request(client, "GET", "/stats?text=");
    same("empty text counts", JSON.parse(empty.body), { text: "", lines: 0, words: 0, bytes: 0 });

    const missing = await request(client, "GET", "/stats");
    same("missing text", [missing.status, JSON.parse(missing.body).error], [422, "missing_text"]);

    const notString = await request(client, "POST", "/stats", '{"text":42}');
    same("non-string text", [notString.status, JSON.parse(notString.body).error], [422, "invalid_json"]);

    const broken = await request(client, "POST", "/stats", "{");
    same("broken json", [broken.status, JSON.parse(broken.body).error], [422, "invalid_json"]);

    const missingMember = await request(client, "POST", "/stats", "{}");
    same("missing member", [missingMember.status, JSON.parse(missingMember.body).error], [422, "missing_text"]);

    const gone = await request(client, "GET", "/nope");
    same("unknown route", [gone.status, JSON.parse(gone.body).detail], [404, "no route for GET /nope"]);

    const wrong = await request(client, "PUT", "/health");
    same("wrong method", [wrong.status, JSON.parse(wrong.body).error], [405, "method_not_allowed"]);

    const tooBig = await request(client, "POST", "/stats", `{"text":"${"x".repeat(64 * 1024)}"}`);
    same("oversized body", [tooBig.status, JSON.parse(tooBig.body).error], [413, "body_too_large"]);

    const concurrent = await Promise.all([
      request(client, "GET", "/stats?text=a"),
      request(client, "GET", "/stats?text=b"),
      request(client, "GET", "/stats?text=c"),
    ]);
    same("three streams", concurrent.map((one) => JSON.parse(one.body).text), ["a", "b", "c"]);
    check("all streams answered", concurrent.every((one) => one.status === 200));
  } finally {
    client.close();
    await stop(server);
  }

  if (failures > 0) {
    throw new Error(`${failures} of ${checks} checks failed`);
  }
  return checks;
}
