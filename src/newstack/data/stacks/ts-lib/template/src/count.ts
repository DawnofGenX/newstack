/** Line, word and byte totals for one input. */
export interface Counts {
  readonly lines: number;
  readonly words: number;
  readonly bytes: number;
}

const NEWLINES = /\n/g;
const WORD = /\S+/g;
const encoder = new TextEncoder();

/**
 * Counts lines, words and bytes the way `wc` does: a line is a `\n`, a word is a
 * maximal run of non-whitespace, and bytes are the UTF-8 length (not the number
 * of characters, so emoji and accented letters cost more than one).
 */
export function countText(text: string): Counts {
  if (typeof text !== "string") {
    throw new TypeError(`countText expects a string, received ${typeof text}`);
  }

  return {
    lines: text.match(NEWLINES)?.length ?? 0,
    words: text.match(WORD)?.length ?? 0,
    bytes: encoder.encode(text).length,
  };
}

/** Adds any number of totals, so a caller can accumulate over several inputs. */
export function sumCounts(...items: Counts[]): Counts {
  return items.reduce<Counts>(
    (total, item) => ({
      lines: total.lines + item.lines,
      words: total.words + item.words,
      bytes: total.bytes + item.bytes,
    }),
    { lines: 0, words: 0, bytes: 0 },
  );
}
