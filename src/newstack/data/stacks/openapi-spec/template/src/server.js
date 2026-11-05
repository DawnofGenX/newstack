import { createServer } from "node:http";

import { countText } from "./count.js";

const MAX_BODY_BYTES = 64 * 1024;

function sendJson(response, status, body) {
  const payload = JSON.stringify(body);
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(payload, "utf8"),
  });
  response.end(payload);
}

function sendError(response, status, error, detail) {
  sendJson(response, status, { error, detail });
}

async function readBody(request) {
  const chunks = [];
  let received = 0;

  for await (const chunk of request) {
    received += chunk.length;
    if (received > MAX_BODY_BYTES) {
      throw new Error("body too large");
    }
    chunks.push(chunk);
  }

  return Buffer.concat(chunks).toString("utf8");
}

/**
 * The handler is exported so tests can drive it in-process, but it is also the thing
 * `node src/server.js` serves: the contract test asserts that what is documented is what
 * a real socket returns.
 */
export function createApp() {
  return async function handle(request, response) {
    const url = new URL(request.url ?? "/", "http://127.0.0.1");

    if (request.method === "GET" && url.pathname === "/health") {
      sendJson(response, 200, { status: "ok" });
      return;
    }

    if (request.method === "GET" && url.pathname === "/stats") {
      const text = url.searchParams.get("text");
      if (text === null) {
        sendError(response, 422, "missing_text", "the `text` query parameter is required");
        return;
      }
      sendJson(response, 200, { text, ...countText(text) });
      return;
    }

    if (request.method === "POST" && url.pathname === "/stats") {
      let raw;
      try {
        raw = await readBody(request);
      } catch {
        sendError(response, 413, "body_too_large", "the request body exceeds 64 KiB");
        return;
      }

      let parsed;
      try {
        parsed = JSON.parse(raw);
      } catch {
        sendError(response, 422, "invalid_json", "the request body must be JSON");
        return;
      }

      const text = parsed === null || typeof parsed !== "object" ? undefined : parsed.text;
      if (typeof text !== "string") {
        sendError(response, 422, "missing_text", "the request body needs a string `text` field");
        return;
      }

      sendJson(response, 200, { text, ...countText(text) });
      return;
    }

    sendError(response, 404, "not_found", `no route for ${request.method} ${url.pathname}`);
  };
}

export function createHttpServer() {
  return createServer(createApp());
}
