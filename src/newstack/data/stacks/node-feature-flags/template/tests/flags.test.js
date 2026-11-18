import test from 'node:test';
import assert from 'node:assert/strict';
import { bucket, resolveFlags, FLAGS } from '../src/flags.js';

test('bucket is stable', () => {
  const a = bucket('new-ui', 'alice');
  const b = bucket('new-ui', 'alice');
  assert.equal(a, b);
});

test('bucket range', () => {
  const b = bucket('new-ui', 'bob');
  assert.ok(b >= 0 && b < 100);
});

test('resolveFlags returns all flags', () => {
  const r = resolveFlags(FLAGS, 'alice');
  assert.ok(Object.prototype.hasOwnProperty.call(r, 'new-ui'));
  assert.ok(Object.prototype.hasOwnProperty.call(r, 'dark-mode'));
});

test('dark-mode always on', () => {
  const r = resolveFlags(FLAGS, 'anyone');
  assert.equal(r['dark-mode'], true);
});
