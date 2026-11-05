import { parse } from "graphql";
import { describe, expect, it } from "vitest";

import { depthOf, MAX_QUERY_DEPTH } from "../src/limits.js";

describe("depthOf", () => {
  it("counts one level per selection set", () => {
    expect(depthOf(parse("{ health { status } }"))).toBe(2);
  });

  it("is one for a query with no nesting", () => {
    expect(depthOf(parse("{ health { status } }"))).toBe(2);
    expect(depthOf(parse("{ __typename }"))).toBe(1);
  });

  it("reports the deepest branch, not the widest", () => {
    const query = parse(`
      {
        health { status }
        stats(text: "x") {
          text
          bytes
        }
      }
    `);
    expect(depthOf(query)).toBe(2);
  });

  it("counts past the limit for a query built to nest", () => {
    expect(depthOf(parse("{ a { b { c { d { e { f { g } } } } } } }"))).toBe(7);
  });

  it("keeps the limit above this schema's own nesting", () => {
    // If this ever fails, the limit is smaller than a query the schema makes natural.
    expect(depthOf(parse("{ stats(text: \"x\") { text } }"))).toBeLessThan(MAX_QUERY_DEPTH);
  });
});
