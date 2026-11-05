import { describe, expect, it } from "vitest";

import { formatCounts } from "./format.js";

const counts = { lines: 2, words: 3, bytes: 14 };

describe("formatCounts", () => {
  it("prints every column at wc's 8-character width", () => {
    expect(formatCounts(counts)).toBe("       2       3      14");
  });

  it("honours a column subset, in the order given", () => {
    expect(formatCounts(counts, { columns: ["words"] })).toBe("       3");
    expect(formatCounts(counts, { columns: ["bytes", "lines"] })).toBe("      14       2");
  });

  it("accepts a narrower width", () => {
    expect(formatCounts(counts, { width: 4 })).toBe("   2   3  14");
  });

  it("appends a label when one is given", () => {
    expect(formatCounts(counts, { label: "README.md" })).toBe("       2       3      14 README.md");
  });

  it("never pads the label", () => {
    expect(formatCounts({ lines: 0, words: 0, bytes: 0 }, { label: "x" })).toBe(
      "       0       0       0 x",
    );
  });
});
