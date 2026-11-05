/**
 * Counting text the way `wc` does: a line is a newline, a word is a maximal run of
 * non-whitespace, and bytes are the UTF-8 encoding, not the number of characters.
 */
export interface Counts {
  readonly lines: number;
  readonly words: number;
  readonly bytes: number;
}

export function countText(text: string): Counts {
  if (typeof text !== "string") {
    throw new TypeError(`countText expects a string, got ${typeof text}`);
  }

  return {
    lines: text.split("\n").length - 1,
    words: text.match(/\S+/gu)?.length ?? 0,
    bytes: Buffer.byteLength(text, "utf8"),
  };
}
