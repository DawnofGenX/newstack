// tests/exporter.test.js — the same contract as `--selftest`, but over a real socket
// on port 0. `node --test tests/*.test.js` (the glob matters on Node 26: a bare
// `tests` argument is treated as a file and MODULE_NOT_FOUNDs).

import assert from "node:assert/strict";
import test, { after, before } from "node:test";

import { createApp } from "../src/app.js";
import { parseExposition, sampleValue } from "../src/exposition.js";
import { Registry } from "../src/metrics.js";
import { createServer, listen, stop } from "../src/server.js";

let server;
let base;
let registry;
let app;

before(async () => {
  registry = new Registry();
  app = createApp({ registry });
  server = createServer(app);
  await listen(server, "127.0.0.1", 0);
  base = `http://127.0.0.1:${server.address().port}`;
});

after(async () => {
  if (server) await stop(server);
});

async function scrape() {
  const response = await fetch(`${base}/metrics`);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type"), /^text\/plain; version=0\.0\.4/);
  return parseExposition(await response.text());
}

test("health answers and the exporter is up", async () => {
  const response = await fetch(`${base}/health`);
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: "ok" });
  const families = await scrape();
  assert.equal(sampleValue(families, "textstat_up"), 1);
});

test("GET /stats counts bytes not characters", async () => {
  const response = await fetch(`${base}/stats?text=h%C3%A9llo%20w%C3%B6rld%0A`);
  assert.deepEqual(await response.json(), { text: "héllo wörld\n", lines: 1, words: 2, bytes: 14 });
});

test("POST /stats accepts JSON and rejects the four shapes differently", async () => {
  const good = await fetch(`${base}/stats`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text: "a b\nc\n" }),
  });
  assert.equal(good.status, 200);
  assert.deepEqual(await good.json(), { text: "a b\nc\n", lines: 2, words: 3, bytes: 6 });

  const cases = [
    ["{}", "missing_text"],
    ["{oops", "invalid_json"],
    ["[1,2,3]", "invalid_body"],
    ['{"text":42}', "invalid_text"],
  ];
  for (const [body, code] of cases) {
    const response = await fetch(`${base}/stats`, { method: "POST", body });
    assert.equal(response.status, 422, `${body} -> ${response.status}`);
    assert.equal((await response.json()).error, code);
  }
});

test("an oversized body is refused before it is parsed", async () => {
  const response = await fetch(`${base}/stats`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text: "x".repeat(70 * 1024) }),
  });
  assert.equal(response.status, 413);
  assert.equal((await response.json()).error, "body_too_large");
});

test("unknown routes 404 with the method and path, wrong methods 405", async () => {
  const gone = await fetch(`${base}/nope`);
  assert.equal(gone.status, 404);
  assert.deepEqual(await gone.json(), {
    error: "not_found",
    detail: "no route for GET /nope",
  });

  const wrong = await fetch(`${base}/health`, { method: "POST" });
  assert.equal(wrong.status, 405);
  assert.equal((await wrong.json()).error, "method_not_allowed");
});

test("label cardinality follows the route pattern, not the raw path", async () => {
  for (const id of ["1", "2", "3"]) {
    const response = await fetch(`${base}/events/${id}`);
    assert.equal(response.status, 200);
    assert.equal((await response.json()).id, id);
  }
  const families = await scrape();
  const events = families
    .get("textstat_requests_total")
    .samples.filter((sample) => sample.labels.route === "/events/:id");
  assert.equal(events.length, 1, "three ids must share one series");
  assert.ok(events[0].value >= 3);
  assert.equal(sampleValue(families, "textstat_events_seen"), 3);
});

test("the scrape is valid Prometheus text and counts itself", async () => {
  const first = await scrape();
  const second = await scrape();
  const series = (families) =>
    sampleValue(families, "textstat_requests_total", {
      method: "GET",
      route: "/metrics",
      status: "200",
    });
  assert.ok(series(second) > series(first), "each scrape must be counted");
  assert.ok(
    second.get("textstat_request_duration_seconds").samples.some(
      (sample) => sample.metric.endsWith("_count") && sample.value >= 1,
    ),
    "a duration histogram must be recorded",
  );
});

test("a broken registry is rejected instead of exported", () => {
  const rogue = new Registry();
  assert.throws(() => rogue.counter("textstat_no_suffix", "wrong"), /must end with _total/);
  assert.throws(() => rogue.observe("textstat_missing", 1), /not a histogram/);
  rogue.histogram("textstat_ok_seconds", "ok", [1]);
  assert.throws(() => rogue.observe("textstat_ok_seconds", -1), /cannot be negative/);
});

test("label values with quotes, backslashes and newlines survive the round trip", () => {
  const local = new Registry();
  local.counter("textstat_weird_total", "escaping");
  const nastiness = 'a\\b"c\nd';
  local.inc("textstat_weird_total", { value: nastiness });
  const parsed = parseExposition(local.render());
  assert.deepEqual(
    parsed.get("textstat_weird_total").samples[0].labels,
    { value: nastiness },
  );
});

test("the parser rejects the four ways a scrape gets silently broken", () => {
  const header = "# HELP x_total help\n# TYPE x_total counter\n";
  assert.throws(() => parseExposition(`${header}x_total 1\n\n`), /blank line/);
  assert.throws(() => parseExposition("# HELP x_total help\n# TYPE x_total counter\nx_total 1"), /newline/);
  assert.throws(
    () => parseExposition(`${header}# TYPE x_total counter\nx_total 1\n`),
    /duplicate TYPE/,
  );
  assert.throws(() => parseExposition(`${header}x_total 1\nx_total 2\n`), /duplicate series/);
});
