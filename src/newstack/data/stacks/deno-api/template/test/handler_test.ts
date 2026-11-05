import { assertEquals } from "@std/assert";
import { handler } from "../src/handler.ts";

async function call(method: string, path: string, body?: string) {
  const response = await handler(
    new Request(`http://localhost${path}`, {
      method,
      body,
      headers: body === undefined
        ? undefined
        : { "content-type": "application/json" },
    }),
  );
  const decoded = await response.json();
  return { status: response.status, body: decoded };
}

Deno.test("GET /health", async () => {
  assertEquals(await call("GET", "/health"), {
    status: 200,
    body: { status: "ok" },
  });
});

Deno.test("GET /stats counts the query parameter", async () => {
  assertEquals(await call("GET", "/stats?text=hello%20world%0A"), {
    status: 200,
    body: { text: "hello world\n", lines: 1, words: 2, bytes: 12 },
  });
});

Deno.test("an empty parameter is empty text, not a missing one", async () => {
  assertEquals(await call("GET", "/stats?text="), {
    status: 200,
    body: { text: "", lines: 0, words: 0, bytes: 0 },
  });
});

Deno.test("GET /stats without a parameter is a 422", async () => {
  assertEquals(await call("GET", "/stats"), {
    status: 422,
    body: { error: "missing_text" },
  });
});

Deno.test("POST /stats counts the body", async () => {
  assertEquals(await call("POST", "/stats", '{"text":"a b\\nc\\n"}'), {
    status: 200,
    body: { text: "a b\nc\n", lines: 2, words: 3, bytes: 6 },
  });
});

Deno.test("POST /stats preserves padding exactly as sent", async () => {
  assertEquals(await call("POST", "/stats", '{"text":"  padded  \\n"}'), {
    status: 200,
    body: { text: "  padded  \n", lines: 1, words: 1, bytes: 11 },
  });
});

Deno.test("POST /stats rejects a non-JSON body with 422", async () => {
  assertEquals(await call("POST", "/stats", "not json"), {
    status: 422,
    body: { error: "invalid_json" },
  });
});

Deno.test("POST /stats rejects a non-string text with 422", async () => {
  assertEquals(await call("POST", "/stats", '{"text":42}'), {
    status: 422,
    body: { error: "missing_text" },
  });
});

Deno.test("an unknown route is a JSON 404", async () => {
  assertEquals(await call("GET", "/nope"), {
    status: 404,
    body: { error: "not_found", detail: "no route for GET /nope" },
  });
});
