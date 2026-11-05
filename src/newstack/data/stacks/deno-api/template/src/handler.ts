import { countsJson, countText } from "./count.ts";

const json = (status: number, body: unknown): Response =>
  Response.json(body, {
    status,
    headers: { "content-type": "application/json" },
  });

/**
 * The whole service as one function: `Request` in, `Response` out.
 *
 * `Deno.serve(handler)` gives you a server from this with no framework, and a test can call
 * it with a constructed `Request` — no port, no readiness loop, no flake.
 */
export async function handler(request: Request): Promise<Response> {
  const url = new URL(request.url);

  if (url.pathname === "/health") {
    return json(200, { status: "ok" });
  }

  if (url.pathname === "/stats") {
    if (request.method === "GET") {
      const text = url.searchParams.get("text");
      if (text === null) return json(422, { error: "missing_text" });
      return json(200, countsJson(text, countText(text)));
    }
    if (request.method === "POST") {
      const body = await request.text();
      let decoded: unknown;
      try {
        decoded = JSON.parse(body);
      } catch {
        return json(422, { error: "invalid_json" });
      }
      if (
        typeof decoded !== "object" || decoded === null ||
        typeof (decoded as { text?: unknown }).text !== "string"
      ) {
        return json(422, { error: "missing_text" });
      }
      const text = (decoded as { text: string }).text;
      return json(200, countsJson(text, countText(text)));
    }
    return json(405, { error: "method_not_allowed" });
  }

  return json(404, {
    error: "not_found",
    detail: `no route for ${request.method} ${url.pathname}`,
  });
}
