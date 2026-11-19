// Byte-level counting: the numbers `wc -l -w -c` prints, for the same bytes.
// Nothing here touches the filesystem, the clock or the process.

export interface Counts {
  lines: number;
  words: number;
  bytes: number;
}

// The bytes wc treats as word separators: space, tab, newline, carriage
// return, vertical tab, form feed.
const WHITESPACE = new Set([32, 9, 10, 13, 11, 12]);

export function countBytes(data: Uint8Array): Counts {
  let lines = 0;
  let words = 0;
  let inWord = false;
  for (const byte of data) {
    if (byte === 10) {
      lines += 1;
      inWord = false;
    } else if (WHITESPACE.has(byte)) {
      inWord = false;
    } else if (!inWord) {
      words += 1;
      inWord = true;
    }
  }
  return { lines, words, bytes: data.length };
}

export function add(left: Counts, right: Counts): Counts {
  return {
    lines: left.lines + right.lines,
    words: left.words + right.words,
    bytes: left.bytes + right.bytes,
  };
}

export type Figure = "lines" | "words" | "bytes";

// The figures a row shows, in the order wc prints them.
export function columns(figures: Figure[], counts: Counts): number[] {
  const values: number[] = [];
  if (figures.includes("lines")) values.push(counts.lines);
  if (figures.includes("words")) values.push(counts.words);
  if (figures.includes("bytes")) values.push(counts.bytes);
  return values;
}
