/** Line, word and byte counts for one piece of text. */
export interface Counts {
  readonly lines: number;
  readonly words: number;
  readonly bytes: number;
}

/**
 * Counts `text` the way `wc` does: a line ends at "\n", a word is a maximal run of
 * non-space characters, and bytes are the UTF-8 length (`héllo` is 5 characters, 6 bytes).
 */
export function countText(text: string): Counts {
  let lines = 0;
  for (const char of text) {
    if (char === "\n") lines += 1;
  }
  return {
    lines,
    words: text.match(/\S+/gu)?.length ?? 0,
    bytes: new TextEncoder().encode(text).length,
  };
}

/** The JSON body every response carries. */
export function countsJson(
  text: string,
  counts: Counts,
): Record<string, unknown> {
  return {
    text,
    lines: counts.lines,
    words: counts.words,
    bytes: counts.bytes,
  };
}
