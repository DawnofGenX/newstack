const SEPARATORS = new Set([0x20, 0x09, 0x0a, 0x0d, 0x0b, 0x0c]);

export function countText(text) {
  const bytes = Buffer.from(text, "utf8");
  let lines = 0;
  let words = 0;
  let inWord = false;
  for (const byte of bytes) {
    if (byte === 0x0a) lines += 1;
    if (SEPARATORS.has(byte)) {
      inWord = false;
    } else if (!inWord) {
      inWord = true;
      words += 1;
    }
  }
  return { lines, words, bytes: bytes.length };
}
