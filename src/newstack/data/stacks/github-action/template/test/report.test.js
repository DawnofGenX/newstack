'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { test } = require('node:test');

const { countFiles, parsePaths, renderMarkdown, totals } = require('../src/report');

function withTempDir(run) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'action-report-'));
  try {
    return run(directory);
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
}

test('parsePaths splits on commas and newlines and trims', () => {
  assert.deepEqual(parsePaths('a.txt, b.txt\nc.txt\n\n'), ['a.txt', 'b.txt', 'c.txt']);
});

test('parsePaths tolerates empty input', () => {
  assert.deepEqual(parsePaths(undefined), []);
  assert.deepEqual(parsePaths(' , \n '), []);
});

test('countFiles reads each path relative to the root', () => {
  withTempDir((directory) => {
    fs.writeFileSync(path.join(directory, 'one.txt'), 'a b\nc\n');
    fs.writeFileSync(path.join(directory, 'two.txt'), '');

    const rows = countFiles(['one.txt', 'two.txt'], directory);

    assert.deepEqual(rows, [
      { path: 'one.txt', lines: 2, words: 3, bytes: 6 },
      { path: 'two.txt', lines: 0, words: 0, bytes: 0 },
    ]);
  });
});

test('countFiles fails loudly on a missing file', () => {
  withTempDir((directory) => {
    assert.throws(() => countFiles(['missing.txt'], directory), /ENOENT/);
  });
});

test('totals adds every column', () => {
  assert.deepEqual(
    totals([
      { lines: 1, words: 2, bytes: 3 },
      { lines: 10, words: 20, bytes: 30 },
    ]),
    { lines: 11, words: 22, bytes: 33 },
  );
});

test('renderMarkdown writes a table with a total row', () => {
  const table = renderMarkdown([{ path: 'a.txt', lines: 2, words: 3, bytes: 6 }], { title: 'Sizes' });

  assert.match(table, /### Sizes/);
  assert.match(table, /\| `a\.txt` \| 2 \| 3 \| 6 \|/);
  assert.match(table, /\| \*\*total\*\* \| \*\*2\*\* \| \*\*3\*\* \| \*\*6\*\* \|/);
  assert.ok(table.startsWith('\n'), 'the table must not glue itself to earlier summary text');
});
