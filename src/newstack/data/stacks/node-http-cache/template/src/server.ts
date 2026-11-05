import { createServer as httpCreateServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { anyMatch, parseTag, parseList, strongTag } from "./etag.js";
import { Library, cacheControl, representation } from "./resource.js";
import type { Document } from "./types.js";

export interface Served {
  status: number;
  headers: Record<string, string>;
  body: string;
}

function header(request: IncomingMessage, name: string): string | undefined {
  const value = request.headers[name];
  return Array.isArray(value) ? value[0] : value;
}

function dateHeader(at: number): string {
  return new Date(at).toUTCString();
}

/**
 * One GET, decided in the RFC 9110 order: If-Match first, then If-None-Match,
 * and only then If-Modified-Since. The order matters: a cache that checks the
 * date first answers 200 to a request that said "I already have this tag".
 */
export function respond(doc: Document, request: { method: string; accept: string; ifMatch?: string; ifNoneMatch?: string; ifModifiedSince?: string }): Served {
  const body = representation(doc, request.accept);
  const etag = strongTag(body);
  const headers: Record<string, string> = {
    etag,
    "cache-control": cacheControl(doc),
  };
  if (doc.varyAccept) {
    headers["vary"] = "accept";
  }

  if (request.method === "PUT") {
    if (request.ifMatch === undefined) {
      return { status: 428, headers, body: "" };
    }
    if (!anyMatch(request.ifMatch, etag, "strong")) {
      return { status: 412, headers, body: "" };
    }
    return { status: 204, headers, body: "" };
  }

  if (request.ifNoneMatch !== undefined) {
    if (anyMatch(request.ifNoneMatch, etag, "weak")) {
      return { status: 304, headers, body: "" };
    }
    return { status: 200, headers: { ...headers, "content-type": contentType(request.accept) }, body };
  }

  if (request.ifMatch !== undefined) {
    if (!anyMatch(request.ifMatch, etag, "strong")) {
      return { status: 412, headers, body: "" };
    }
  }

  if (request.ifModifiedSince !== undefined) {
    const since = Date.parse(request.ifModifiedSince);
    if (!Number.isNaN(since) && Math.floor(doc.changedAt / 1000) <= Math.floor(since / 1000)) {
      return { status: 304, headers, body: "" };
    }
  }

  return {
    status: 200,
    headers: { ...headers, "content-type": contentType(request.accept), "content-length": String(Buffer.byteLength(body)) },
    body,
  };
}

function contentType(accept: string): string {
  return accept.includes("text/plain") ? "text/plain; charset=utf-8" : "application/json";
}

export interface Handle {
  server: Server;
  port: number;
  close: () => Promise<void>;
}

export function createServer(library: Library, port = 0): Promise<Handle> {
  const server = httpCreateServer((request: IncomingMessage, response: ServerResponse) => {
    const path = new URL(request.url ?? "/", "http://localhost").pathname;
    const doc = library.get(path);
    if (doc === undefined) {
      response.writeHead(404, { "content-type": "text/plain" });
      response.end(`no document at ${path}\n`);
      return;
    }
    const accept = header(request, "accept") ?? "*/*";
    const conditional: {
      method: string;
      accept: string;
      ifMatch?: string;
      ifNoneMatch?: string;
      ifModifiedSince?: string;
    } = { method: request.method ?? "GET", accept };
    const ifMatch = header(request, "if-match");
    const ifNoneMatch = header(request, "if-none-match");
    const ifModifiedSince = header(request, "if-modified-since");
    if (ifMatch !== undefined) {
      conditional.ifMatch = ifMatch;
    }
    if (ifNoneMatch !== undefined) {
      conditional.ifNoneMatch = ifNoneMatch;
    }
    if (ifModifiedSince !== undefined) {
      conditional.ifModifiedSince = ifModifiedSince;
    }
    const sent = respond(doc, conditional);
    response.writeHead(sent.status, sent.headers);
    response.end(sent.status === 304 || sent.status === 204 ? undefined : sent.body);
  });

  return new Promise((resolve, reject) => {
    server.on("error", reject);
    server.listen(port, "127.0.0.1", () => {
      const address = server.address();
      const bound = typeof address === "object" && address !== null ? address.port : port;
      resolve({
        server,
        port: bound,
        close: () =>
          new Promise<void>((done) => {
            // Keep-alive sockets would otherwise hold close() open forever.
            server.closeAllConnections();
            server.close(() => done());
          }),
      });
    });
  });
}

export { parseTag, parseList };
