'use strict';

/**
 * Counts text the way `wc` does: newlines for lines, runs of non-whitespace for
 * words, UTF-8 bytes for bytes.
 *
 * @param {string} text
 * @returns {{lines: number, words: number, bytes: number}}
 */
function countText(text) {
  if (typeof text !== 'string') {
    throw new TypeError(`countText expects a string, received ${typeof text}`);
  }

  let lines = 0;
  for (const character of text) {
    if (character === '\n') {
      lines += 1;
    }
  }

  const words = (text.match(/\S+/g) || []).length;

  return { lines, words, bytes: Buffer.byteLength(text, 'utf8') };
}

module.exports = { countText };
