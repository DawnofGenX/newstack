/** Word/line/byte counting with `wc` semantics over the raw UTF-8 bytes. */
export interface Counts {
  readonly lines: number;
  readonly words: number;
  readonly bytes: number;
}

const SEPARATORS = new Set([0x20, 0x09, 0x0a, 0x0d, 0x0b, 0x0c]);

export function countText(text: string): Counts {
  const raw = Buffer.from(text, "utf8");
  let lines = 0;
  let words = 0;
  let inWord = false;
  for (const byte of raw) {
    if (byte === 0x0a) lines += 1;
    if (SEPARATORS.has(byte)) {
      inWord = false;
    } else if (!inWord) {
      inWord = true;
      words += 1;
    }
  }
  return { lines, words, bytes: raw.length };
}
