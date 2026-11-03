// Pure counting: no I/O, no globals. The entry point reads the bytes; every
// decision about what a line, a word and a byte are lives here, so the tests
// can drive this module directly.

export interface Counts {
  lines: number;
  words: number;
  bytes: number;
}

const WHITESPACE = new Set([" ", "\t", "\n", "\v", "\f", "\r"]);

/**
 * Counts newlines, whitespace-separated words and raw bytes.
 *
 * Lines follow `wc -l`: the number of "\n" characters, so a final line without
 * a terminator is not counted. Words are maximal runs of non-whitespace
 * characters. Bytes are the length of the UTF-8 encoding of the text, which is
 * what `wc -c` reports for the file the text was read from. This is the same
 * contract as the other newstack CLI stacks.
 */
export function count(text: string): Counts {
  let lines = 0;
  let words = 0;
  let inWord = false;
  for (const ch of text) {
    if (ch === "\n") {
      lines += 1;
      inWord = false;
    } else if (WHITESPACE.has(ch)) {
      inWord = false;
    } else if (!inWord) {
      words += 1;
      inWord = true;
    }
  }
  return { lines, words, bytes: new TextEncoder().encode(text).length };
}

/** Adds two totals field by field, so several files can be reported as one. */
export function add(left: Counts, right: Counts): Counts {
  return {
    lines: left.lines + right.lines,
    words: left.words + right.words,
    bytes: left.bytes + right.bytes,
  };
}
