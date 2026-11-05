import { describe, expect, it } from "vitest";

import { createApp } from "../src/app.js";

const app = createApp();

async function json(response: Response): Promise<unknown> {
  return await response.json();
}

describe("GET /health", () => {
  it("answers ok", async () => {
    const response = await app.request("/health");
    expect(response.status).toBe(200);
    expect(await json(response)).toEqual({ status: "ok" });
  });
});

describe("GET /stats", () => {
  it("counts the text query parameter", async () => {
    const response = await app.request("/stats?text=hello%20world%0A");
    expect(response.status).toBe(200);
    expect(await json(response)).toEqual({
      text: "hello world\n",
      lines: 1,
      words: 2,
      bytes: 12,
    });
  });

  it("counts an empty value as zeroes rather than rejecting it", async () => {
    const response = await app.request("/stats?text=");
    expect(response.status).toBe(200);
    expect(await json(response)).toEqual({ text: "", lines: 0, words: 0, bytes: 0 });
  });

  it("is 422 when the parameter is missing", async () => {
    const response = await app.request("/stats");
    expect(response.status).toBe(422);
  });
});

describe("POST /stats", () => {
  it("counts a JSON body exactly as sent", async () => {
    const response = await app.request("/stats", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: "  padded  \n" }),
    });
    expect(response.status).toBe(200);
    // Trimming or normalising the body here would silently change the byte count.
    expect(await json(response)).toEqual({
      text: "  padded  \n",
      lines: 1,
      words: 1,
      bytes: 11,
    });
  });

  it("is 422 when the field is missing", async () => {
    const response = await app.request("/stats", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({}),
    });
    expect(response.status).toBe(422);
  });

  it("is 422 when the field is not a string", async () => {
    const response = await app.request("/stats", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: 42 }),
    });
    expect(response.status).toBe(422);
  });

  it("is 422 when the body is not JSON", async () => {
    const response = await app.request("/stats", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "not json",
    });
    expect(response.status).toBe(422);
  });
});

describe("unknown routes", () => {
  it("is a JSON 404", async () => {
    const response = await app.request("/nope");
    expect(response.status).toBe(404);
    expect(await json(response)).toEqual({ error: "not_found" });
  });
});
