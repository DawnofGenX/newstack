// app.js — routing plus the metrics each request feeds. The router returns the
// ROUTE PATTERN it matched, and that pattern (never the raw path) is the label:
// `/events/17` and `/events/18` must collapse into one series, or scrape
// cardinality ends up following the traffic.

import { countText } from "./counts.js";

const METHODS = {
  "/health": ["GET"],
  "/stats": ["GET", "POST"],
  "/metrics": ["GET"],
  "/events/:id": ["GET"],
};

const MAX_BODY = 64 * 1024;
const DURATION = "textstat_request_duration_seconds";

export function json(status, payload) {
  return {
    status,
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  };
}

export function matchRoute(pathname) {
  if (Object.hasOwn(METHODS, pathname)) return { pattern: pathname, params: {} };
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length === 2 && parts[0] === "events") {
    return { pattern: "/events/:id", params: { id: parts[1] } };
  }
  return null;
}

export function queryText(search) {
  const params = new URLSearchParams(search);
  return params.has("text") ? params.get("text") : null;
}

// Read with a cap enforced WHILE reading: trusting content-length alone lets a
// chunked client stream gigabytes in, and reading first then checking means the
// memory was already spent.
async function readCapped(request, limit) {
  const declared = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(declared) && declared > limit) return { tooLarge: true };
  if (!request.body) return { raw: "" };
  const reader = request.body.getReader();
  const chunks = [];
  let total = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > limit) {
      await reader.cancel();
      return { tooLarge: true };
    }
    chunks.push(Buffer.from(value));
  }
  return { raw: Buffer.concat(chunks).toString("utf8") };
}

export function createApp({ registry, startedAt = Date.now() }) {
  registry.counter("textstat_requests_total", "HTTP requests handled, by matched route pattern.");
  registry.counter("textstat_text_bytes_total", "UTF-8 bytes of text that was counted.");
  registry.counter("textstat_lines_total", "Newline characters counted.");
  registry.counter("textstat_words_total", "Words counted.");
  registry.counter("textstat_errors_total", "Requests rejected, labelled by machine code.");
  registry.gauge("textstat_inflight_requests", "Requests currently being handled.");
  registry.gauge("textstat_up", "1 when the process is serving.");
  registry.gauge("textstat_events_seen", "Distinct event ids this process has answered.");
  registry.histogram(DURATION, "Wall time spent handling a request, by matched route.", [
    0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1,
  ]);
  registry.set("textstat_up", 1);

  const seen = new Set();

  function note(route, method, status) {
    registry.inc("textstat_requests_total", { method, route, status: String(status) });
  }

  function reject(route, method, status, code, detail) {
    registry.inc("textstat_errors_total", { code });
    note(route, method, status);
    return json(status, detail ? { error: code, detail } : { error: code });
  }

  async function handle(request, matched, route) {
    const url = new URL(request.url);
    const method = request.method;

    if (!matched) {
      return reject("unmatched", method, 404, "not_found", `no route for ${method} ${url.pathname}`);
    }
    if (!METHODS[route].includes(method)) {
      return reject(route, method, 405, "method_not_allowed");
    }

    if (route === "/health") {
      registry.set("textstat_up", 1);
      note(route, method, 200);
      return json(200, { status: "ok" });
    }

    if (route === "/metrics") {
      // Counted BEFORE rendering so the scrape can see itself land; a scrape that
      // is rendered first always looks one request behind.
      note(route, method, 200);
      return {
        status: 200,
        headers: { "content-type": "text/plain; version=0.0.4; charset=utf-8" },
        body: registry.render(),
      };
    }

    if (route === "/events/:id") {
      seen.add(matched.params.id);
      registry.set("textstat_events_seen", seen.size);
      note(route, method, 200);
      return json(200, { id: matched.params.id, kind: "viewed" });
    }

    // /stats
    let text;
    if (method === "GET") {
      text = queryText(url.search);
      if (text === null) return reject(route, method, 422, "missing_text");
    } else {
      const read = await readCapped(request, MAX_BODY);
      if (read.tooLarge) return reject(route, method, 413, "body_too_large");
      const raw = read.raw;
      let payload;
      try {
        payload = JSON.parse(raw);
      } catch {
        return reject(route, method, 422, "invalid_json");
      }
      if (payload === null || typeof payload !== "object" || Array.isArray(payload)) {
        return reject(route, method, 422, "invalid_body");
      }
      if (!("text" in payload)) return reject(route, method, 422, "missing_text");
      if (typeof payload.text !== "string") return reject(route, method, 422, "invalid_text");
      text = payload.text;
    }

    const counts = countText(text);
    registry.inc("textstat_text_bytes_total", {}, counts.bytes);
    registry.inc("textstat_lines_total", {}, counts.lines);
    registry.inc("textstat_words_total", {}, counts.words);
    note(route, method, 200);
    return json(200, { text, ...counts });
  }

  return {
    async serve(request) {
      const matched = matchRoute(new URL(request.url).pathname);
      const route = matched ? matched.pattern : "unmatched";
      registry.add("textstat_inflight_requests", {}, 1);
      const started = process.hrtime.bigint();
      try {
        return await handle(request, matched, route);
      } finally {
        const seconds = Number(process.hrtime.bigint() - started) / 1e9;
        registry.observe(DURATION, seconds, { route });
        registry.add("textstat_inflight_requests", {}, -1);
      }
    },
    registry,
    startedAt,
  };
}
