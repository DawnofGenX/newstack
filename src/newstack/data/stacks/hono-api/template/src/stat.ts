/**
 * wc-style counting. Kept free of Hono and of Node globals so it is a plain function
 * that the tests can hit with a string, and the routes stay thin enough to read.
 */

export interface Counts {
  readonly lines: number;
  readonly words: number;
  readonly bytes: number;
}

const WORD = /\S+/g;

export function countText(text: string): Counts {
  if (typeof text !== "string") {
    throw new TypeError(`countText expects a string, got ${typeof text}`);
  }
  return {
    // A line is a newline, exactly like `wc -l`: a trailing newline closes the last
    // line instead of opening an empty one.
    lines: text.split("\n").length - 1,
    words: text.match(WORD)?.length ?? 0,
    // Bytes, not characters: "héllo" is 5 characters and 6 bytes.
    bytes: new TextEncoder().encode(text).length,
  };
}
