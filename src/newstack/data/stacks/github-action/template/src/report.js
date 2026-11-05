'use strict';

const fs = require('node:fs');
const path = require('node:path');

const { countText } = require('./count');

/**
 * Splits the `paths` input on commas and newlines.
 *
 * @param {string} raw
 * @returns {string[]}
 */
function parsePaths(raw) {
  return String(raw ?? '')
    .split(/[\n,]+/)
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
}

/**
 * Reads and counts every path, relative to `root`.
 *
 * @param {string[]} paths
 * @param {string} [root]
 * @returns {Array<{path: string, lines: number, words: number, bytes: number}>}
 */
function countFiles(paths, root = process.cwd()) {
  return paths.map((relative) => {
    const text = fs.readFileSync(path.join(root, relative), 'utf8');
    return { path: relative, ...countText(text) };
  });
}

/**
 * @param {Array<{lines: number, words: number, bytes: number}>} rows
 * @returns {{lines: number, words: number, bytes: number}}
 */
function totals(rows) {
  return rows.reduce(
    (sum, row) => ({
      lines: sum.lines + row.lines,
      words: sum.words + row.words,
      bytes: sum.bytes + row.bytes,
    }),
    { lines: 0, words: 0, bytes: 0 },
  );
}

/**
 * Renders a Markdown table for the job summary.
 *
 * The leading blank line keeps the table from being glued to whatever text the
 * caller appended to the summary before us.
 *
 * @param {Array<{path: string, lines: number, words: number, bytes: number}>} rows
 * @param {{title?: string}} [options]
 * @returns {string}
 */
function renderMarkdown(rows, { title = 'File sizes' } = {}) {
  const sum = totals(rows);
  const lines = [
    '',
    `### ${title}`,
    '',
    '| File | Lines | Words | Bytes |',
    '| --- | ---: | ---: | ---: |',
    ...rows.map((row) => `| \`${row.path}\` | ${row.lines} | ${row.words} | ${row.bytes} |`),
    `| **total** | **${sum.lines}** | **${sum.words}** | **${sum.bytes}** |`,
    '',
  ];

  return lines.join('\n');
}

module.exports = { parsePaths, countFiles, totals, renderMarkdown };
