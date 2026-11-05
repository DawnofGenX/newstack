import { describe, expect, it } from "vitest";

import { countText } from "../src/stat.js";

describe("countText", () => {
  it("counts like wc on a plain sentence", () => {
    expect(countText("hello world\n")).toEqual({ lines: 1, words: 2, bytes: 12 });
  });

  it("treats an empty string as all zeroes", () => {
    expect(countText("")).toEqual({ lines: 0, words: 0, bytes: 0 });
  });

  it("counts a blank line as a line but never as a word", () => {
    expect(countText("\n\nx\n")).toEqual({ lines: 3, words: 1, bytes: 4 });
  });

  it("counts a final line without a newline", () => {
    expect(countText("abc")).toEqual({ lines: 0, words: 1, bytes: 3 });
  });

  it("counts UTF-8 bytes, not characters", () => {
    expect(countText("héllo wörld\n")).toEqual({ lines: 1, words: 2, bytes: 14 });
    expect(countText("🙂\n")).toEqual({ lines: 1, words: 1, bytes: 5 });
  });

  it("rejects non-strings instead of coercing them", () => {
    expect(() => countText(42 as unknown as string)).toThrow(TypeError);
  });
});
