/** Pure request->reply logic, so it can be tested without a socket. */
import { countText, type Counts } from "./counts.js";

export interface Reply {
  readonly status: number;
  readonly body: unknown;
}

export interface StatsBody extends Counts {
  readonly text: string;
}

const JSON_ESCAPES: Record<string, string> = {
  '"': '\\"',
  "\\": "\\\\",
  "\n": "\\n",
  "\r": "\\r",
  "\t": "\\t",
  "\b": "\\b",
  "\f": "\\f",
};

/** Escape a string exactly the way JSON.stringify would, for the hand-built replies. */
export function jsonQuote(value: string): string {
  let out = '"';
  for (const char of value) {
    const escape = JSON_ESCAPES[char];
    if (escape !== undefined) {
      out += escape;
      continue;
    }
    const code = char.codePointAt(0) ?? 0;
    out += code < 0x20 ? `\\u${code.toString(16).padStart(4, "0")}` : char;
  }
  return `${out}"`;
}

export function statsBody(text: string): StatsBody {
  const counts = countText(text);
  // Key order matters: text, lines, words, bytes.
  return { text, lines: counts.lines, words: counts.words, bytes: counts.bytes };
}

/** Percent-decode a query parameter: '+' is a space, %XX is one raw byte. */
export function percentDecode(value: string): string {
  const bytes: number[] = [];
  for (let index = 0; index < value.length; index += 1) {
    const char = value[index];
    if (char === "+") {
      bytes.push(0x20);
      continue;
    }
    if (char === "%" && index + 2 < value.length) {
      const hex = value.slice(index + 1, index + 3);
      if (/^[0-9a-fA-F]{2}$/.test(hex)) {
        bytes.push(Number.parseInt(hex, 16));
        index += 2;
        continue;
      }
    }
    const encoded = Buffer.from(char ?? "", "utf8");
    for (const byte of encoded) bytes.push(byte);
  }
  return Buffer.from(bytes).toString("utf8");
}

/** First occurrence wins; a leading '?' is dropped; no parameter means undefined. */
export function queryText(target: string): string | undefined {
  const mark = target.indexOf("?");
  if (mark === -1) return undefined;
  let found: string | undefined;
  for (const pair of target.slice(mark + 1).split("&")) {
    if (pair === "") continue;
    const equals = pair.indexOf("=");
    const name = equals === -1 ? pair : pair.slice(0, equals);
    const raw = equals === -1 ? "" : pair.slice(equals + 1);
    if (percentDecode(name) === "text" && found === undefined) found = percentDecode(raw);
  }
  return found;
}

export interface RequestShape {
  readonly method: string;
  readonly target: string;
  readonly body: string | undefined;
}

type JsonRead = { kind: "text"; text: string } | { kind: "missing" } | { kind: "invalid" };

/** Read {"text": …} out of a JSON body without trusting it to be well formed. */
export function readTextMember(raw: string): JsonRead {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return { kind: "invalid" };
  }
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    return { kind: "invalid" };
  }
  const member = (parsed as Record<string, unknown>)["text"];
  if (member === undefined) return { kind: "missing" };
  if (typeof member !== "string") return { kind: "invalid" };
  return { kind: "text", text: member };
}

export function route(request: RequestShape): Reply {
  const { method, target } = request;
  const path = target.split("?")[0] ?? "";

  if (path === "/health") {
    if (method !== "GET") {
      return { status: 405, body: { error: "method_not_allowed", detail: `${method} /health is read-only` } };
    }
    return { status: 200, body: { status: "ok" } };
  }

  if (path === "/stats") {
    if (method === "GET") {
      const text = queryText(target) ?? "";
      return { status: 200, body: statsBody(text) };
    }
    if (method === "POST") {
      const raw = request.body ?? "";
      const read = readTextMember(raw);
      if (read.kind === "invalid") return { status: 422, body: { error: "invalid_json" } };
      if (read.kind === "missing") return { status: 422, body: { error: "missing_text" } };
      return { status: 200, body: statsBody(read.text) };
    }
    return { status: 405, body: { error: "method_not_allowed", detail: `${method} /stats is read-only` } };
  }

  return {
    status: 404,
    body: { error: "not_found", detail: `no route for ${method} ${path}` },
  };
}
