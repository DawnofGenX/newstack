import { Hono } from "hono";

import { countText } from "./stat.js";

/**
 * The app is built as a value, not started here: `app.request()` can then be handed a
 * URL and return a Response in-process, so the tests never open a socket.
 */
export function createApp(): Hono {
  const app = new Hono();

  app.get("/health", (c) => c.json({ status: "ok" }));

  app.get("/stats", (c) => {
    const text = c.req.query("text");
    if (text === undefined) {
      return c.json({ error: "the `text` query parameter is required" }, 422);
    }
    return c.json({ text, ...countText(text) });
  });

  app.post("/stats", async (c) => {
    let body: unknown;
    try {
      body = await c.req.json();
    } catch {
      return c.json({ error: "the request body must be JSON" }, 422);
    }
    const text = (body as { text?: unknown } | null)?.text;
    // A missing field and a non-string are the same client mistake: 422, not 500.
    if (typeof text !== "string") {
      return c.json({ error: "`text` must be a string" }, 422);
    }
    return c.json({ text, ...countText(text) });
  });

  app.notFound((c) => c.json({ error: "not_found" }, 404));

  return app;
}
