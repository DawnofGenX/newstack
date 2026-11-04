// Counting is where the bugs live, so it gets the most tests.

import { add, columns, countBytes } from "../src/counts.ts";

function count(text: string): ReturnType<typeof countBytes> {
  return countBytes(new TextEncoder().encode(text));
}

function equal(actual: unknown, expected: unknown, message: string): void {
  const left = JSON.stringify(actual);
  const right = JSON.stringify(expected);
  if (left !== right) throw new Error(`${message}: got ${left}, want ${right}`);
}

Deno.test("plain text", () => {
  equal(count("alpha beta\ngamma\n"), { lines: 2, words: 3, bytes: 17 }, "plain text");
});

Deno.test("no trailing newline", () => {
  equal(count("alpha beta\ngamma"), { lines: 1, words: 3, bytes: 16 }, "no trailing newline");
});

Deno.test("empty input", () => {
  equal(count(""), { lines: 0, words: 0, bytes: 0 }, "empty input");
});

Deno.test("utf-8 counts bytes, not characters", () => {
  equal(count("h\u00e9llo w\u00f6rld\n"), { lines: 1, words: 2, bytes: 14 }, "utf-8");
});

Deno.test("tab, vertical tab and form feed separate words", () => {
  equal(count("a\tb\nc\vd\re\n"), { lines: 2, words: 5, bytes: 10 }, "control characters");
});

Deno.test("blank lines count", () => {
  equal(count("one\ntwo\n\nthree\n"), { lines: 4, words: 3, bytes: 15 }, "blank lines");
});

Deno.test("totals add", () => {
  equal(add({ lines: 1, words: 2, bytes: 3 }, { lines: 10, words: 20, bytes: 30 }),
    { lines: 11, words: 22, bytes: 33 }, "add");
});

Deno.test("columns follow wc's order, not the flags'", () => {
  equal(columns(["bytes", "lines"], { lines: 1, words: 2, bytes: 3 }), [1, 3],
    "columns");
  equal(columns(["words"], { lines: 1, words: 2, bytes: 3 }), [2], "one column");
});

Deno.test("whitespace-only input still counts bytes", () => {
  const data = new Uint8Array(300).fill(32);
  data[0] = 10;
  data[150] = 10;
  equal(countBytes(data), { lines: 2, words: 0, bytes: 300 }, "whitespace");
});
