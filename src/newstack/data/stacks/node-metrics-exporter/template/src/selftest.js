// selftest.js — offline assertions, no socket, no filesystem. Every check names the
// rule it protects so a failure reads as an explanation rather than a stack trace.

import { createApp } from "./app.js";
import { parseExposition, sampleValue } from "./exposition.js";
import { Registry } from "./metrics.js";

let checks = 0;

function ok(condition, what) {
  checks += 1;
  if (!condition) throw new Error(`selftest FAIL: ${what}`);
}

function eq(actual, expected, what) {
  ok(
    JSON.stringify(actual) === JSON.stringify(expected),
    `${what}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
  );
}

function throws(fn, needle, what) {
  checks += 1;
  try {
    fn();
  } catch (error) {
    ok(String(error.message).includes(needle), `${what}: message was "${error.message}"`);
    return;
  }
  throw new Error(`selftest FAIL: ${what}: expected a throw`);
}

async function call(app, path, init) {
  const answer = await app.serve(new Request(`http://127.0.0.1${path}`, init));
  const parsed = answer.headers["content-type"].includes("json") ? JSON.parse(answer.body) : answer.body;
  return { ...answer, json: parsed };
}

export function runSelftest() {
  // --- the registry enforces the format, not the caller --------------------
  const registry = new Registry();
  throws(() => registry.counter("textstat_hits", "no suffix"), "must end with _total", "counter suffix");
  throws(
    () => registry.gauge("textstat_bucket", "reserved"),
    "reserved suffix",
    "gauge suffix",
  );
  registry.counter("textstat_demo_total", "demo counter");
  throws(() => registry.inc("textstat_demo_total", {}, -1), "only go up", "negative counter");
  registry.gauge("textstat_demo_gauge", "demo gauge");
  throws(() => registry.inc("textstat_demo_gauge"), "not a counter", "inc on a gauge");
  throws(() => registry.set("textstat_demo_gauge", NaN), "must be finite", "NaN gauge");
  const again = registry.counter("textstat_demo_total", "again");
  eq(
    again.samples.size,
    registry.counter("textstat_demo_total", "third time").samples.size,
    "re-registering a counter returns the same family",
  );
  throws(
    () => registry.gauge("textstat_demo_total", "type change"),
    "already registered",
    "type change",
  );

  registry.set("textstat_demo_gauge", 1);
  registry.add("textstat_demo_gauge", {}, 2);
  const firstRender = registry.render();
  eq(sampleValue(parseExposition(firstRender), "textstat_demo_gauge"), 3, "add() moves a gauge");
  eq(registry.render(), firstRender, "render is deterministic");
  eq(
    firstRender.split("\n").filter((line) => line.startsWith("# TYPE textstat_demo_total")).length,
    1,
    "one TYPE line per family",
  );

  // label escaping: a backslash, a quote and a newline all survive the round trip
  registry.counter("textstat_labels_total", "escaping");
  const nasty = 'a\\b"c\nd';
  registry.inc("textstat_labels_total", { value: nasty });
  const escaped = registry.render();
  ok(escaped.includes('value="a\\\\b\\"c\\nd"'), "label values are escaped once");
  const parsedLabels = parseExposition(escaped).get("textstat_labels_total").samples[0].labels;
  eq(parsedLabels.value, nasty, "escaped labels round-trip");

  // histogram invariants
  const hist = new Registry();
  hist.histogram("textstat_probe_seconds", "probe", [0.5, 0.1]);
  hexpect(hist);
  function hexpect(target) {
    target.observe("textstat_probe_seconds", 0.05, { route: "/a" });
    target.observe("textstat_probe_seconds", 0.2, { route: "/a" });
    target.observe("textstat_probe_seconds", 2, { route: "/a" });
    const families = parseExposition(target.render());
    eq(sampleValue(families, "textstat_probe_seconds_bucket", { route: "/a", le: "0.1" }), 1, "le=0.1");
    eq(sampleValue(families, "textstat_probe_seconds_bucket", { route: "/a", le: "0.5" }), 2, "le=0.5");
    eq(
      sampleValue(families, "textstat_probe_seconds_bucket", { route: "/a", le: "+Inf" }),
      sampleValue(families, "textstat_probe_seconds_count", { route: "/a" }),
      "+Inf equals _count",
    );
    eq(sampleValue(families, "textstat_probe_seconds_count", { route: "/a" }), 3, "three observations");
  }
  throws(
    () => new Registry().histogram("textstat_bad_seconds", "bad", [Infinity]),
    "finite buckets",
    "Infinity bucket rejected",
  );
  throws(
    () => {
      const bad = new Registry();
      bad.histogram("textstat_bad_seconds", "bad", [1]);
      bad.observe("textstat_bad_seconds", -1);
    },
    "cannot be negative",
    "negative duration rejected",
  );

  // --- the app contract ----------------------------------------------------
  const appRegistry = new Registry();
  const app = createApp({ registry: appRegistry });

  return (async () => {
    const health = await call(app, "/health");
    eq([health.status, health.json], [200, { status: "ok" }], "GET /health");

    const get = await call(app, "/stats?text=a%20b%0Ac");
    eq([get.status, get.json.lines, get.json.words, get.json.bytes], [200, 1, 3, 5], "GET /stats");

    const utf8 = await call(app, "/stats?text=h%C3%A9llo%20w%C3%B6rld%0A");
    eq([utf8.json.lines, utf8.json.words, utf8.json.bytes], [1, 2, 14], "bytes are UTF-8 bytes");

    const post = await call(app, "/stats", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: "a b\nc\n" }),
    });
    eq([post.status, post.json.lines, post.json.words, post.json.bytes], [200, 2, 3, 6], "POST /stats");

    const missing = await call(app, "/stats", { method: "POST", body: "{}" });
    eq([missing.status, missing.json.error], [422, "missing_text"], "missing text is 422");

    const invalid = await call(app, "/stats", { method: "POST", body: "{oops" });
    eq([invalid.status, invalid.json.error], [422, "invalid_json"], "bad JSON is 422");

    const array = await call(app, "/stats", { method: "POST", body: "[1,2,3]" });
    eq([array.status, array.json.error], [422, "invalid_body"], "a JSON array is not a body");

    const wrongType = await call(app, "/stats", {
      method: "POST",
      body: JSON.stringify({ text: 42 }),
    });
    eq([wrongType.status, wrongType.json.error], [422, "invalid_text"], "non-string text is 422");

    const noQuery = await call(app, "/stats");
    eq([noQuery.status, noQuery.json.error], [422, "missing_text"], "GET without text is 422");

    const gone = await call(app, "/nope");
    eq(
      [gone.status, gone.json.detail],
      [404, "no route for GET /nope"],
      "unknown route",
    );

    const wrongMethod = await call(app, "/health", { method: "POST" });
    eq([wrongMethod.status, wrongMethod.json.error], [405, "method_not_allowed"], "wrong method");

    await call(app, "/events/7");
    const second = await call(app, "/events/8");
    eq(second.json.id, "8", "GET /events/:id echoes the id");

    // --- the scrape ----------------------------------------------------------
    const scrape = await call(app, "/metrics");
    eq(scrape.status, 200, "GET /metrics");
    ok(
      scrape.headers["content-type"].startsWith("text/plain; version=0.0.4"),
      "metrics content type carries the version",
    );
    const families = parseExposition(scrape.body);
    eq(sampleValue(families, "textstat_up"), 1, "textstat_up is 1");
    // The request rendering this payload is itself in flight: an honest exporter says 1.
    eq(sampleValue(families, "textstat_inflight_requests"), 1, "a scrape sees itself in flight");
    eq(
      sampleValue(parseExposition(appRegistry.render()), "textstat_inflight_requests"),
      0,
      "inflight returns to zero once the scrape is answered",
    );

    const events = families.get("textstat_requests_total").samples.filter(
      (sample) => sample.labels.route === "/events/:id",
    );
    eq(events.length, 1, "two ids collapse into one series (route pattern, not raw path)");
    eq(events[0].value, 2, "both /events requests counted once");

    const stats = families.get("textstat_requests_total").samples.filter(
      (sample) => sample.labels.route === "/stats",
    );
    ok(stats.length >= 3, "every status on /stats is its own series");
    ok(
      stats.every((sample) => sample.labels.status !== undefined),
      "status is always labelled",
    );

    const duration = families.get("textstat_request_duration_seconds").samples;
    ok(duration.length >= 1, "a duration histogram was observed");
    eq(
      sampleValue(families, "textstat_lines_total"),
      1 + 1 + 2,
      "line counter tracks every counted text",
    );

    const second_scrape = parseExposition((await call(app, "/metrics")).body);
    ok(
      sampleValue(second_scrape, "textstat_requests_total", {
        method: "GET",
        route: "/metrics",
        status: "200",
      }) >= 2,
      "the scrape counts itself",
    );

    return checks;
  })();
}
