import { describe, expect, it } from "vitest";

import { yoga } from "../src/yoga.js";

interface GraphQLResponse {
  data?: Record<string, unknown> | null;
  errors?: { message: string; extensions?: { code?: string } }[];
}

async function run(
  query: string,
  variables?: Record<string, unknown>,
): Promise<{ status: number; body: GraphQLResponse; contentType: string | null }> {
  const response = await yoga.fetch("http://localhost/graphql", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ query, variables }),
  });

  return {
    status: response.status,
    body: (await response.json()) as GraphQLResponse,
    contentType: response.headers.get("content-type"),
  };
}

describe("the GraphQL endpoint", () => {
  it("answers a health query off the schema, not a hand-written route", async () => {
    const { status, body, contentType } = await run("{ health { status } }");
    expect(status).toBe(200);
    expect(contentType).toContain("application/json");
    expect(body).toEqual({ data: { health: { status: "ok" } } });
  });

  it("returns the counts for a variable", async () => {
    const { body } = await run("query ($text: String!) { stats(text: $text) { text lines words bytes } }", {
      text: "hello world\n",
    });
    expect(body).toEqual({
      data: { stats: { text: "hello world\n", lines: 1, words: 2, bytes: 12 } },
    });
  });

  it("treats blank text as a zero, not a missing value", async () => {
    const { body } = await run('{ stats(text: "") { lines words bytes } }');
    expect(body).toEqual({ data: { stats: { lines: 0, words: 0, bytes: 0 } } });
  });

  it("counts bytes, not characters", async () => {
    const { body } = await run('{ stats(text: "héllo wörld\\n") { bytes words lines } }');
    expect(body.data?.stats).toEqual({ bytes: 14, words: 2, lines: 1 });
  });

  it("rejects a missing required variable before the resolver runs", async () => {
    const { status, body } = await run("query ($text: String!) { stats(text: $text) { bytes } }");
    // A malformed *request* (missing variable) is a 400 ...
    expect(status).toBe(400);
    expect(body.errors?.[0]?.message).toContain('Variable "$text"');
    expect(body.errors?.[0]?.message).toContain("Expected a value of non-null type");
  });

  it("reports a bad literal argument as a validation error, with a 200", async () => {
    // ... while a bad *query* is answered with 200 + an errors array, which is what the
    // GraphQL-over-HTTP spec asks for once the request itself parsed.
    const { status, body } = await run("{ stats(text: 42) { bytes } }");
    expect(status).toBe(200);
    expect(body.data).toBeUndefined();
    expect(body.errors?.[0]?.extensions?.code).toBe("GRAPHQL_VALIDATION_FAILED");
    expect(body.errors?.[0]?.message).toContain("String cannot represent a non string value: 42");
  });

  it("names the missing argument when the query omits it", async () => {
    const { body } = await run("{ stats { bytes } }");
    expect(body.errors?.[0]?.message).toContain('Argument "Query.stats(text:)" of type "String!" is required');
  });

  it("refuses a query deeper than the limit, with a code a client can branch on", async () => {
    const { body } = await run("{ a { b { c { d { e { f { g } } } } } } }");
    const codes = body.errors?.map((error) => error.extensions?.code);
    expect(codes).toContain("QUERY_TOO_DEEP");
  });

  it("still answers introspection, because the depth limit only counts selections", async () => {
    const { body } = await run("{ __schema { queryType { name } } }");
    expect(body).toEqual({ data: { __schema: { queryType: { name: "Query" } } } });
  });
});
