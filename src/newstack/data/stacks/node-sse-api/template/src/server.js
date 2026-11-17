// The HTTP side: three routes, no framework.
//
//   GET  /health              -> {"status":"ok","subscribers":N,"events":M}
//   GET  /events?topic=t      -> text/event-stream (Last-Event-ID resumes)
//   POST /publish             -> {"id":N}    body {"topic":"t","data":...}

import { createServer as createHttpServer } from "node:http";

import { EventLog } from "./events.js";
import { ALL_TOPICS, Hub } from "./hub.js";
import { assertTopic } from "./frame.js";

const MAX_BODY = 64 * 1024;

function sendJson(res, status, body) {
  const text = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(text),
  });
  res.end(text);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY) {
        reject(Object.assign(new Error("body too large"), { status: 413 }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

export function createServer({ log = new EventLog(), heartbeatMs = 15000 } = {}) {
  const hub = new Hub(log, { heartbeatMs });

  async function handle(req, res) {
    const url = new URL(req.url ?? "/", "http://127.0.0.1");
    const path = url.pathname;

    if (path === "/health") {
      if (req.method !== "GET") return sendJson(res, 405, { error: "method_not_allowed", allow: "GET" });
      return sendJson(res, 200, { status: "ok", subscribers: hub.size, events: log.size });
    }

    if (path === "/events") {
      if (req.method !== "GET") return sendJson(res, 405, { error: "method_not_allowed", allow: "GET" });
      const topic = url.searchParams.get("topic") ?? ALL_TOPICS;
      if (topic !== ALL_TOPICS) {
        try {
          assertTopic(topic);
        } catch (err) {
          return sendJson(res, 400, { error: "bad_topic", detail: err.message });
        }
      }
      const lastId = req.headers["last-event-id"] ?? url.searchParams.get("last_id");
      res.writeHead(200, {
        "content-type": "text/event-stream; charset=utf-8",
        "cache-control": "no-cache, no-transform",
        connection: "keep-alive",
        // nginx buffers proxied responses by default; that turns a stream into
        // one large response delivered at the end.
        "x-accel-buffering": "no",
      });
      res.flushHeaders?.();
      const subscribers = hub.subscribe(res, { topic, lastId });
      // The close listener, not the write, is what frees the slot: a client
      // that vanishes never produces a failed write.
      res.on("close", () => hub.remove(res));
      process.stdout.write(`subscriber joined (${subscribers} open)\n`);
      return undefined;
    }

    if (path === "/publish") {
      if (req.method !== "POST") return sendJson(res, 405, { error: "method_not_allowed", allow: "POST" });
      let payload;
      try {
        payload = JSON.parse(await readBody(req));
      } catch (err) {
        const status = err.status ?? 400;
        return sendJson(res, status, { error: status === 413 ? "body_too_large" : "bad_json", detail: err.message });
      }
      if (payload === null || typeof payload !== "object") {
        return sendJson(res, 400, { error: "bad_body", detail: "expected a JSON object" });
      }
      try {
        assertTopic(payload.topic);
      } catch (err) {
        return sendJson(res, 400, { error: "bad_topic", detail: err.message });
      }
      const event = hub.publish(payload.topic, payload.data ?? null);
      return sendJson(res, 202, { id: event.id, subscribers: hub.size });
    }

    return sendJson(res, 404, {
      error: "not_found",
      detail: `no route for ${req.method} ${path}`,
    });
  }

  const server = createHttpServer((req, res) => {
    handle(req, res).catch((err) => {
      if (res.headersSent) {
        res.destroy();
        return;
      }
      sendJson(res, 500, { error: "internal", detail: err.message });
    });
  });

  server.log = log;
  server.hub = hub;
  server.on("close", () => hub.close());
  return server;
}
