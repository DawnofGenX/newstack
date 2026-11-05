import { countsJson, countText } from "./count.ts";

const JSON_HEADERS = { "content-type": "application/json" } as const;

function json(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), { status, headers: JSON_HEADERS });
}

function notFound(request: Request, url: URL): Response {
  return json(
    { error: "not_found", detail: `no route for ${request.method} ${url.pathname}` },
    404,
  );
}

/**
 * The whole application: a `Request` in, a `Response` out. `Bun.serve` accepts this
 * directly as `fetch`, and a test can call it with a constructed request, so no port
 * is opened while the suite runs.
 */
export async function handler(request: Request): Promise<Response> {
  const url = new URL(request.url);

  if (url.pathname === "/health") {
    if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
    return json({ status: "ok" }, 200);
  }

  if (url.pathname === "/stats") {
    if (request.method === "GET") {
      const text = url.searchParams.get("text");
      if (text === null) return json({ error: "missing_text" }, 422);
      return json(countsJson(text, countText(text)), 200);
    }
    if (request.method === "POST") {
      let body: unknown;
      try {
        body = await request.json();
      } catch {
        return json({ error: "invalid_json" }, 422);
      }
      const text = (body as { text?: unknown } | null)?.text;
      if (typeof text !== "string") return json({ error: "missing_text" }, 422);
      return json(countsJson(text, countText(text)), 200);
    }
    return json({ error: "method_not_allowed" }, 405);
  }

  return notFound(request, url);
}
