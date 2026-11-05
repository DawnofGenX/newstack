#!/usr/bin/env node
/** Fixture server: the page, its assets, one JSON endpoint, and a client-side route. */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, resolve } from "node:path";

import { countText } from "./app/lib/counts.mjs";

const HERE = resolve(import.meta.dirname);
const APP = join(HERE, "app");
const PORT = Number.parseInt(process.env.PORT ?? "8080", 10);
const HOST = process.env.HOST ?? "127.0.0.1";

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

function json(response, status, body) {
  const payload = JSON.stringify(body);
  response.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  response.end(payload);
}

const server = createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", `http://${request.headers.host ?? "localhost"}`);
  const path = url.pathname;

  if (path === "/api/stats") {
    json(response, 200, countText(url.searchParams.get("text") ?? ""));
    return;
  }
  if (path === "/api/health") {
    json(response, 200, { status: "ok" });
    return;
  }
  if (path.startsWith("/api/")) {
    json(response, 404, { error: "not_found", detail: `no endpoint for ${request.method} ${path}` });
    return;
  }

  const file = path === "/" || path === "/about" ? join(APP, "index.html") : join(APP, path.replace(/^\//, ""));
  if (!file.startsWith(APP)) {
    response.writeHead(403).end();
    return;
  }
  try {
    const body = await readFile(file);
    response.writeHead(200, { "content-type": TYPES[extname(file)] ?? "application/octet-stream" });
    response.end(body);
  } catch {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end(`no such file: ${path}\n`);
  }
});

server.listen(PORT, HOST, () => {
  process.stdout.write(`fixture server on http://${HOST}:${PORT}\n`);
});

for (const signal of ["SIGTERM", "SIGINT"]) {
  process.on(signal, () => {
    server.close(() => process.exit(0));
  });
}
