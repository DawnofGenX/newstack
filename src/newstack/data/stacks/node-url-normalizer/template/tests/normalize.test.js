import { test } from 'node:test';
import assert from 'node:assert/strict';
import { normalizeUrl } from '../src/normalize.js';

test('lowercases host and drops default port', () => {
  assert.equal(normalizeUrl('https://Example.COM:443/a/'), 'https://example.com/a');
});

test('sorts query params', () => {
  assert.equal(normalizeUrl('https://example.com/x?b=2&a=1'), 'https://example.com/x?a=1&b=2');
});

test('drops tracking params', () => {
  assert.equal(normalizeUrl('https://example.com/x?utm_source=x&a=1'), 'https://example.com/x?a=1');
});
