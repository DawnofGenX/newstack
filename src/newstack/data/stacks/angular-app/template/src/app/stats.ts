/** `wc`-style counting over the raw UTF-8 bytes, shared by the component and its tests. */
export interface Counts {
  readonly lines: number;
  readonly words: number;
  readonly bytes: number;
}

const SEPARATORS = new Set([0x20, 0x09, 0x0a, 0x0d, 0x0b, 0x0c]);

export function countText(text: string): Counts {
  const raw = new TextEncoder().encode(text);
  let lines = 0;
  let words = 0;
  let inWord = false;
  for (const byte of raw) {
    if (byte === 0x0a) {
      lines += 1;
    }
    if (SEPARATORS.has(byte)) {
      inWord = false;
      continue;
    }
    if (!inWord) {
      inWord = true;
      words += 1;
    }
  }
  return { lines, words, bytes: raw.length };
}

/** "3 lines · 5 words · 21 bytes", the summary the page shows. */
export function summarize(counts: Counts): string {
  const plural = (count: number, noun: string) => `${count} ${noun}${count === 1 ? "" : "s"}`;
  return [plural(counts.lines, "line"), plural(counts.words, "word"), plural(counts.bytes, "byte")].join(" \u00b7 ");
}
