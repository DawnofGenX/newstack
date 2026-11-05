// The routing table. Everything that answers a request lives here so the HTTP
// server in server.js stays about sockets and shutdown.
import { MAX_SIZE } from "./store.js";

const JSON_LIMIT = 64 * 1024;

function send(res, status, payload, headers = {}) {
  const body = Buffer.from(JSON.stringify(payload));
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": body.length,
    ...headers,
  });
  res.end(body);
}

function fail(res, status, error, detail, extra = {}) {
  send(res, status, { error, detail, ...extra });
}

// readJson caps the body while it streams: trusting Content-Length means a
// client can send nothing and still make the server allocate.
async function readJson(req) {
  const chunks = [];
  let total = 0;
  for await (const chunk of req) {
    total += chunk.length;
    if (total > JSON_LIMIT) {
      const error = new Error("too large");
      error.code = "too_large";
      throw error;
    }
    chunks.push(chunk);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    const error = new Error("invalid json");
    error.code = "invalid_json";
    throw error;
  }
}

function parseCreate(payload) {
  if (payload === null || typeof payload !== "object") {
    return { error: "invalid_json", detail: "the body must be a JSON object" };
  }
  if (typeof payload.name !== "string" || payload.name.trim() === "") {
    return { error: "missing_name", detail: "name must be a non-empty string" };
  }
  if (!Number.isInteger(payload.size) || payload.size < 1) {
    return { error: "invalid_size", detail: "size must be a positive integer" };
  }
  if (payload.size > MAX_SIZE) {
    return { error: "too_large", detail: `the limit is ${MAX_SIZE} bytes` };
  }
  return { name: payload.name, size: payload.size };
}

function publicSession(session) {
  const view = {
    id: session.id,
    name: session.name,
    size: session.size,
    received: session.received,
    offset: session.received,
    complete: session.complete,
  };
  if (session.digest) view.sha256 = session.digest;
  return view;
}

export function route(store) {
  return async function handle(req, res) {
    let url;
    try {
      url = new URL(req.url, "http://upload.invalid");
    } catch {
      fail(res, 400, "bad_request", "the request target is not a URL");
      return;
    }
    const segments = url.pathname.split("/").filter(Boolean);

    try {
      if (url.pathname === "/health") {
        if (req.method !== "GET") return methodNotAllowed(res, req.method);
        return send(res, 200, { status: "ok", sessions: store.count() });
      }

      if (segments[0] === "uploads" && segments.length === 1) {
        if (req.method !== "POST") return methodNotAllowed(res, req.method);
        let payload;
        try {
          payload = await readJson(req);
        } catch (error) {
          if (error.code === "too_large") {
            return fail(res, 413, "body_too_large", "the limit is 64 KiB");
          }
          return fail(res, 422, "invalid_json", "the request body must be JSON");
        }
        const parsed = parseCreate(payload);
        if (parsed.error) return fail(res, parsed.error === "too_large" ? 413 : 422, parsed.error, parsed.detail);
        const session = store.create(parsed.name, parsed.size);
        await store.save();
        return send(res, 201, publicSession(session));
      }

      if (segments[0] === "uploads" && segments.length === 3 && segments[2] === "content") {
        if (req.method !== "GET") return methodNotAllowed(res, req.method);
        const session = store.get(segments[1]);
        if (!session) return unknownUpload(res, segments[1]);
        if (!session.complete) {
          return fail(res, 409, "incomplete", "the upload has not finished", {
            received: session.received,
            size: session.size,
          });
        }
        const bytes = await store.read(session.id);
        res.writeHead(200, {
          "Content-Type": "application/octet-stream",
          "Content-Length": bytes.length,
          "X-Content-Sha256": session.digest,
        });
        return res.end(bytes);
      }

      if (segments[0] === "uploads" && segments.length === 2) {
        const session = store.get(segments[1]);
        if (!session) return unknownUpload(res, segments[1]);
        if (req.method === "GET") return send(res, 200, publicSession(session));
        if (req.method === "DELETE") {
          await store.remove(session.id);
          res.writeHead(204);
          return res.end();
        }
        if (req.method === "PUT") return await receive(req, res, store, session, url);
        return methodNotAllowed(res, req.method);
      }

      return fail(res, 404, "not_found", `no route for ${req.method} ${url.pathname}`);
    } catch (error) {
      // A handler that throws must still answer: an unhandled rejection would
      // leave the socket hanging until the client's own timeout.
      fail(res, 500, "internal_error", String(error && error.message ? error.message : error));
    }
  };
}

async function receive(req, res, store, session, url) {
  const raw = url.searchParams.get("offset");
  if (raw === null) return fail(res, 422, "invalid_offset", "offset is required");
  if (!/^\d+$/.test(raw)) return fail(res, 422, "invalid_offset", "offset must be a byte count");
  const offset = Number(raw);
  // The offset is the client's claim about what it already sent. Accepting a
  // mismatch would either drop bytes or duplicate them, and the file would pass
  // its length check while being wrong.
  if (offset !== session.received) {
    return fail(res, 409, "offset_mismatch", "offset does not match the bytes received", {
      expected: session.received,
      got: offset,
    });
  }
  if (session.complete) {
    return fail(res, 409, "already_complete", "the upload already has every byte", {
      expected: session.size,
      got: offset,
    });
  }

  let accepted = 0;
  for await (const chunk of req) {
    if (session.received + chunk.length > session.size) {
      return fail(res, 413, "too_large", "the chunk passes the declared size", {
        size: session.size,
        received: session.received,
      });
    }
    await store.write(session, chunk);
    accepted += chunk.length;
  }

  if (accepted === 0) {
    return fail(res, 422, "empty_chunk", "a chunk must carry at least one byte");
  }
  return send(res, 200, publicSession(session));
}

function methodNotAllowed(res, method) {
  return fail(res, 405, "method_not_allowed", `${method} is not allowed here`);
}

function unknownUpload(res, id) {
  return fail(res, 404, "unknown_upload", `no upload with id ${id}`);
}
