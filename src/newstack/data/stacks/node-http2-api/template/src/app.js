import { countText } from "./counts.js";
import { queryText, readTextMember } from "./json.js";

const MAX_BODY = 64 * 1024;

const ROUTES = new Map([
  ["/health", ["GET"]],
  ["/stats", ["GET", "POST"]],
]);

function reply(stream, status, payload) {
  const body = JSON.stringify(payload);
  stream.respond({
    ":status": status,
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
  });
  stream.end(body);
}

function statsBody(text) {
  const counts = countText(text);
  return { text, lines: counts.lines, words: counts.words, bytes: counts.bytes };
}

function readBody(stream) {
  return new Promise((resolve) => {
    const chunks = [];
    let size = 0;
    let settled = false;
    stream.on("data", (chunk) => {
      if (settled) return;
      size += chunk.length;
      if (size > MAX_BODY) {
        settled = true;
        resolve({ tooLarge: true });
        return;
      }
      chunks.push(chunk);
    });
    stream.on("end", () => {
      if (settled) return;
      settled = true;
      resolve({ tooLarge: false, raw: Buffer.concat(chunks).toString("utf8") });
    });
    stream.on("error", () => {
      if (settled) return;
      settled = true;
      resolve({ aborted: true });
    });
  });
}

export function createApp({ log = () => {} } = {}) {
  let requests = 0;

  async function handle(stream, headers) {
    requests += 1;
    const method = headers[":method"];
    const target = headers[":path"] || "/";
    const at = target.indexOf("?");
    const path = at === -1 ? target : target.slice(0, at);
    const search = at === -1 ? "" : target.slice(at);

    const allowed = ROUTES.get(path);
    if (allowed === undefined) {
      log(`${method} ${path} 404`);
      reply(stream, 404, { error: "not_found", detail: `no route for ${method} ${path}` });
      return;
    }
    if (!allowed.includes(method)) {
      log(`${method} ${path} 405`);
      reply(stream, 405, { error: "method_not_allowed", detail: `${method} ${path} takes ${allowed.join("/")}` });
      return;
    }

    if (path === "/health") {
      reply(stream, 200, { status: "ok", protocol: "h2", requests });
      return;
    }

    if (method === "GET") {
      const text = queryText(search);
      if (text === null) {
        reply(stream, 422, { error: "missing_text", detail: 'add ?text=... or POST {"text":"..."}' });
        return;
      }
      reply(stream, 200, statsBody(text));
      return;
    }

    const body = await readBody(stream);
    if (body.tooLarge) {
      reply(stream, 413, { error: "body_too_large", detail: `the body must stay under ${MAX_BODY} bytes` });
      return;
    }
    if (body.aborted) {
      log(`${method} ${path} aborted`);
      return;
    }
    const member = readTextMember(body.raw);
    if (member.kind === "invalid") {
      reply(stream, 422, { error: "invalid_json", detail: "the body must be a JSON object whose text is a string" });
      return;
    }
    if (member.kind === "missing") {
      reply(stream, 422, { error: "missing_text", detail: "the body needs a text member" });
      return;
    }
    reply(stream, 200, statsBody(member.text));
  }

  return {
    handle(stream, headers) {
      const done = handle(stream, headers);
      stream.on("error", () => {});
      return done.catch((error) => {
        log(`handler error: ${error.message}`);
        if (!stream.headersSent) reply(stream, 500, { error: "internal_error", detail: error.message });
        else stream.close(2);
      });
    },
    get requests() {
      return requests;
    },
  };
}
