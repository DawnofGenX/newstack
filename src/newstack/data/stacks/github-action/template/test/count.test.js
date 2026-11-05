'use strict';

const assert = require('node:assert/strict');
const { test } = require('node:test');

const { countText } = require('../src/count');

const cases = [
  ['', { lines: 0, words: 0, bytes: 0 }],
  ['one two\n', { lines: 1, words: 2, bytes: 8 }],
  ['one two\nthree\n', { lines: 2, words: 3, bytes: 14 }],
  ['  padded  \n', { lines: 1, words: 1, bytes: 11 }],
  ['no trailing newline', { lines: 0, words: 3, bytes: 19 }],
  ['héllo wörld\n', { lines: 1, words: 2, bytes: 14 }],
];

for (const [text, expected] of cases) {
  test(`counts ${JSON.stringify(text)} the way wc does`, () => {
    assert.deepEqual(countText(text), expected);
  });
}

test('blank lines are lines', () => {
  assert.deepEqual(countText('\n\nx\n'), { lines: 3, words: 1, bytes: 4 });
});

test('whitespace only text has no words but keeps its bytes', () => {
  assert.deepEqual(countText('  \t '), { lines: 0, words: 0, bytes: 4 });
});

test('rejects a non-string instead of guessing', () => {
  assert.throws(() => countText(null), TypeError);
});
