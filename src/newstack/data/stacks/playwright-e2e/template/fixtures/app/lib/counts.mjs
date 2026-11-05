/** `wc` semantics over the UTF-8 bytes; shared by the page and the fixture server. */
const SEPARATORS = new Set([0x20, 0x09, 0x0a, 0x0d, 0x0b, 0x0c]);

export function countText(text) {
  const raw = new TextEncoder().encode(text);
  let lines = 0;
  let words = 0;
  let inWord = false;
  for (const byte of raw) {
    if (byte === 0x0a) lines += 1;
    if (SEPARATORS.has(byte)) {
      inWord = false;
      continue;
    }
    if (!inWord) {
      inWord = true;
      words += 1;
    }
  }
  return { text, lines, words, bytes: raw.length };
}
