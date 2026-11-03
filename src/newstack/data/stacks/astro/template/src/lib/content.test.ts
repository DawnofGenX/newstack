import { describe, expect, it } from "vitest";

import { formatCount } from "./content";

describe("formatCount", () => {
  it("uses the singular noun for exactly one", () => {
    expect(formatCount(1, "feature")).toBe("1 feature");
  });

  it("uses the plural noun for zero and for many", () => {
    expect(formatCount(0, "feature")).toBe("0 features");
    expect(formatCount(3, "feature")).toBe("3 features");
  });

  it("accepts an irregular plural", () => {
    expect(formatCount(2, "entry", "entries")).toBe("2 entries");
  });

  it("rejects negative and fractional counts", () => {
    expect(() => formatCount(-1, "feature")).toThrow(RangeError);
    expect(() => formatCount(1.5, "feature")).toThrow(RangeError);
  });
});
