// server.js — node:http plumbing around the framework-free app.
//
// `app.serve()` speaks the fetch API (a Request in, an answer out) because that is
// what every runtime has converged on — but a node IncomingMessage is NOT a
// Request: `request.url` is a bare path, so `new URL(request.url)` throws
// `TypeError: Invalid URL` and every route answers 500. The bridge below builds the
// Request the app expects, including a streaming body (duplex: "half" is required
// for any request with a body).

import { createServer as createHttpServer } from "node:http";
import { Readable } from "node:stream";

const BODYLESS = new Set(["GET", "HEAD", "DELETE", "OPTIONS"]);

export function toRequest(request) {
  const origin = `http://${request.headers.host || "127.0.0.1"}`;
  const init = { method: request.method, headers: request.headers };
  if (!BODYLESS.has(request.method)) {
    // Streamed, not buffered: the app enforces its own size cap while reading.
    init.body = Readable.toWeb(request);
    init.duplex = "half";
  }
  return new Request(new URL(request.url ?? "/", origin), init);
}

export function createServer(app) {
  const server = createHttpServer(async (request, response) => {
    let answer;
    try {
      answer = await app.serve(toRequest(request));
    } catch (error) {
      console.error("unhandled:", error);
      answer = {
        status: 500,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ error: "internal_error" }),
      };
    }
    // content-length, never chunked: a scraper that gets a truncated body cannot
    // tell a network failure from a malformed exposition.
    response.writeHead(answer.status, {
      ...answer.headers,
      "content-length": Buffer.byteLength(answer.body),
    });
    response.end(answer.body);
  });
  server.headersTimeout = 10_000;
  server.requestTimeout = 30_000;
  return server;
}

export function listen(server, host, port) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, host, () => resolve(server.address().port));
  });
}

export function stop(server) {
  return new Promise((resolve) => {
    server.close(() => resolve());
    server.closeIdleConnections?.();
    setTimeout(() => server.closeAllConnections?.(), 2000).unref();
  });
}
