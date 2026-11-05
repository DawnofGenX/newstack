import { describe, expect, it } from "vitest";

import { countText } from "../src/stat.js";

describe("countText", () => {
  it("counts a single line", () => {
    expect(countText("hello world\n")).toEqual({ lines: 1, words: 2, bytes: 12 });
  });

  it("counts nothing in an empty string", () => {
    expect(countText("")).toEqual({ lines: 0, words: 0, bytes: 0 });
  });

  it("does not count a trailing partial line as a line", () => {
    expect(countText("abc")).toEqual({ lines: 0, words: 1, bytes: 3 });
  });

  it("keeps blank lines in the line count", () => {
    expect(countText("\n\nx\n")).toEqual({ lines: 3, words: 1, bytes: 4 });
  });

  it("counts whitespace as bytes but not as words", () => {
    expect(countText("  \t ")).toEqual({ lines: 0, words: 0, bytes: 4 });
  });

  it("counts UTF-8 bytes, not characters", () => {
    expect(countText("héllo wörld\n")).toEqual({ lines: 1, words: 2, bytes: 14 });
  });

  it("rejects a non-string", () => {
    // @ts-expect-error — the point of the guard is that JavaScript callers can still do this
    expect(() => countText(42)).toThrow(TypeError);
  });
});
