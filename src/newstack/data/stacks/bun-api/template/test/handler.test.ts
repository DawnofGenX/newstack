import { describe, expect, test } from "bun:test";

import { handler } from "../src/handler.ts";

const base = "http://127.0.0.1:8080";

async function get(path: string): Promise<Response> {
  return await handler(new Request(`${base}${path}`));
}

async function post(body: string, contentType = "application/json"): Promise<Response> {
  return await handler(
    new Request(`${base}/stats`, {
      method: "POST",
      headers: { "content-type": contentType },
      body,
    }),
  );
}

describe("handler", () => {
  test("answers health", async () => {
    const response = await get("/health");
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ status: "ok" });
  });

  test("counts the query parameter", async () => {
    const response = await get("/stats?text=hello%20world%0A");
    expect(await response.json()).toEqual({
      text: "hello world\n",
      lines: 1,
      words: 2,
      bytes: 12,
    });
  });

  test("treats an empty parameter as empty text", async () => {
    const response = await get("/stats?text=");
    expect(await response.json()).toEqual({ text: "", lines: 0, words: 0, bytes: 0 });
  });

  test("rejects a missing parameter", async () => {
    const response = await get("/stats");
    expect(response.status).toBe(422);
    expect(await response.json()).toEqual({ error: "missing_text" });
  });

  test("counts a posted body", async () => {
    const response = await post(JSON.stringify({ text: "a b\nc\n" }));
    expect(await response.json()).toEqual({
      text: "a b\nc\n",
      lines: 2,
      words: 3,
      bytes: 6,
    });
  });

  test("preserves padding exactly as sent", async () => {
    const response = await post(JSON.stringify({ text: "  padded  \n" }));
    expect(await response.json()).toEqual({
      text: "  padded  \n",
      lines: 1,
      words: 1,
      bytes: 11,
    });
  });

  test("rejects a body that is not JSON with 422", async () => {
    const response = await post("not json");
    expect(response.status).toBe(422);
    expect(await response.json()).toEqual({ error: "invalid_json" });
  });

  test("rejects a non-string text", async () => {
    const response = await post(JSON.stringify({ text: 42 }));
    expect(response.status).toBe(422);
    expect(await response.json()).toEqual({ error: "missing_text" });
  });

  test("an unknown route is a JSON 404", async () => {
    const response = await get("/nope");
    expect(response.status).toBe(404);
    expect(await response.json()).toEqual({
      error: "not_found",
      detail: "no route for GET /nope",
    });
  });
});
