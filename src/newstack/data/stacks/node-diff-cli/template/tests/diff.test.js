import test from 'node:test';
import assert from 'node:assert/strict';
import { makePatch, computeStat } from '../src/diff.js';

test('makePatch contains header', () => {
  const p = makePatch('a.txt', 'b.txt', 'line1\n', 'line1\nline2\n');
  assert.match(p, /--- a.txt/);
  assert.match(p, /\+\+\+ b.txt/);
  assert.match(p, /\+line2/);
});

test('computeStat counts', () => {
  const s = computeStat('a\nb\n', 'a\nc\nd\n');
  assert.equal(s.added, 2);
  assert.equal(s.removed, 1);
});
