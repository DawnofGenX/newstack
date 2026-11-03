import { beforeEach, describe, expect, it } from "vitest";

import { COUNTER_KEY, clampCount, readCounter, writeCounter } from "./counter-store";

beforeEach(() => {
  localStorage.clear();
});

describe("counter contract", () => {
  it("uses the shared storage key", () => {
    expect(COUNTER_KEY).toBe("newstack:counter");
  });

  it("clamps garbage to a non-negative integer", () => {
    expect(clampCount(-3)).toBe(0);
    expect(clampCount(2.9)).toBe(2);
    expect(clampCount(Number.NaN)).toBe(0);
    expect(clampCount(Number.POSITIVE_INFINITY)).toBe(0);
    expect(clampCount("7")).toBe(7);
    expect(clampCount(null)).toBe(0);
  });

  it("round-trips through storage", () => {
    writeCounter(3);
    expect(readCounter()).toBe(3);
    expect(localStorage.getItem(COUNTER_KEY)).toBe("3");
  });

  it("ignores a tampered value", () => {
    localStorage.setItem(COUNTER_KEY, "not-a-number");
    expect(readCounter()).toBe(0);
    localStorage.setItem(COUNTER_KEY, "-5");
    expect(readCounter()).toBe(0);
  });
});
