export type Stats = {
  text: string;
  lines: number;
  words: number;
  bytes: number;
};

// Word breaks in the contract are the ASCII whitespace bytes, exactly.
const SEPARATORS = new Set([" ", "\t", "\n", "\r", "\x0b", "\x0c"]);

/** Count newlines, whitespace-separated word runs, and UTF-8 bytes. */
export function stats(text: string): Stats {
  let lines = 0;
  let words = 0;
  let inWord = false;
  for (const character of text) {
    if (character === "\n") lines += 1;
    if (SEPARATORS.has(character)) {
      inWord = false;
    } else if (!inWord) {
      inWord = true;
      words += 1;
    }
  }
  return { text, lines, words, bytes: new TextEncoder().encode(text).length };
}
