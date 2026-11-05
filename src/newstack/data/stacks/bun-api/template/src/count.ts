/**
 * Counting rules, shared by every route. This module knows nothing about HTTP.
 *
 * `lines` ends at every "\n", `words` is a maximal run of non-space characters and
 * `bytes` is the UTF-8 length, so the numbers match `wc` for the same file.
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
  let lines = 0;
  for (let i = 0; i < text.length; i += 1) {
    if (text[i] === "\n") lines += 1;
  }
  return {
    lines,
    words: text.match(/\S+/gu)?.length ?? 0,
    bytes: new TextEncoder().encode(text).length,
  };
}

export function countsJson(
  text: string,
  counts: Counts,
): { text: string; lines: number; words: number; bytes: number } {
  return { text, lines: counts.lines, words: counts.words, bytes: counts.bytes };
}
