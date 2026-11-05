import { describe, expect, test } from "bun:test";

import { countText } from "../src/count.ts";

describe("countText", () => {
  const cases: Array<[string, string, number, number, number]> = [
    ["a line", "hello world\n", 1, 2, 12],
    ["empty text", "", 0, 0, 0],
    ["blank lines", "\n\nx\n", 3, 1, 4],
    ["whitespace only", "  \t ", 0, 0, 4],
    ["no trailing newline", "abc", 0, 1, 3],
    ["multi-byte characters", "héllo wörld\n", 1, 2, 14],
    ["an emoji", "🙂\n", 1, 1, 5],
  ];

  for (const [name, text, lines, words, bytes] of cases) {
    test(`counts ${name}`, () => {
      expect(countText(text)).toEqual({ lines, words, bytes });
    });
  }

  test("refuses a non-string", () => {
    expect(() => countText(42 as unknown as string)).toThrow(TypeError);
  });
});
