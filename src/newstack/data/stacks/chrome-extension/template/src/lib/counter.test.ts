import { describe, expect, it } from "vitest";

import { COUNT_STORAGE_KEY, formatCount, nextCount, resetCount } from "./counter";

describe("nextCount", () => {
  it("increments by one", () => {
    expect(nextCount(0)).toBe(1);
    expect(nextCount(41)).toBe(42);
  });

  it("floors and clamps negative input", () => {
    expect(nextCount(-5)).toBe(1);
    expect(nextCount(2.9)).toBe(3);
  });

  it("treats non-finite input as zero", () => {
    expect(nextCount(Number.NaN)).toBe(1);
    expect(nextCount(Number.POSITIVE_INFINITY)).toBe(1);
  });
});

describe("resetCount", () => {
  it("returns zero", () => {
    expect(resetCount()).toBe(0);
  });
});

describe("formatCount", () => {
  it("renders a label", () => {
    expect(formatCount(0)).toBe("Popup clicks: 0");
    expect(formatCount(7)).toBe("Popup clicks: 7");
  });

  it("never renders negative or NaN values", () => {
    expect(formatCount(-3)).toBe("Popup clicks: 0");
    expect(formatCount(Number.NaN)).toBe("Popup clicks: 0");
  });
});

describe("storage key", () => {
  it("is stable", () => {
    expect(COUNT_STORAGE_KEY).toBe("count");
  });
});
