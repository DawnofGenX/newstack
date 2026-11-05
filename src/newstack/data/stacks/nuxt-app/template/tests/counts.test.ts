import { describe, expect, it } from "vitest";
import { stats } from "../lib/counts";

describe("stats", () => {
  it("counts a trailing newline as a line", () => {
    expect(stats("a b\n")).toEqual({ text: "a b\n", lines: 1, words: 2, bytes: 4 });
  });

  it("counts UTF-8 bytes, not UTF-16 code units", () => {
    expect(stats("héllo wörld\n")).toMatchObject({ lines: 1, words: 2, bytes: 14 });
  });

  it("treats a run of separators as one break", () => {
    expect(stats("  a\t\tb  ")).toMatchObject({ words: 2 });
  });

  it("counts no newline in a string without one", () => {
    expect(stats("one line")).toMatchObject({ lines: 0, words: 2 });
  });

  it("counts the empty string as all zeroes", () => {
    expect(stats("")).toEqual({ text: "", lines: 0, words: 0, bytes: 0 });
  });
});
