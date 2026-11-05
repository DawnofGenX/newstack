import { assertEquals } from "@std/assert";
import { countText } from "../src/count.ts";

const cases: Array<
  [string, string, { lines: number; words: number; bytes: number }]
> = [
  ["one line", "hello world\n", { lines: 1, words: 2, bytes: 12 }],
  ["empty", "", { lines: 0, words: 0, bytes: 0 }],
  ["blank lines", "\n\nx\n", { lines: 3, words: 1, bytes: 4 }],
  ["whitespace only", "  \t ", { lines: 0, words: 0, bytes: 4 }],
  ["no trailing newline", "abc", { lines: 0, words: 1, bytes: 3 }],
  ["utf-8", "héllo wörld\n", { lines: 1, words: 2, bytes: 14 }],
  ["emoji", "🙂\n", { lines: 1, words: 1, bytes: 5 }],
];

Deno.test("countText matches wc", () => {
  for (const [name, text, want] of cases) {
    assertEquals(countText(text), want, name);
  }
});

Deno.test("countText counts astral-plane characters as one word", () => {
  assertEquals(countText("🙂 🙂\n").words, 2);
});
