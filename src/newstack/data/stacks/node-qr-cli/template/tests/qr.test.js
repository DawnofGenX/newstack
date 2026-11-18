import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { generatePng, renderTerminal } from '../src/qr.js';

test('generatePng writes a PNG with magic bytes and nonzero size', async () => {
  const file = path.join(os.tmpdir(), `qr-${Date.now()}.png`);
  await generatePng('hello newstack', file);
  const buf = fs.readFileSync(file);
  assert.equal(buf[0], 0x89);
  assert.equal(buf[1], 0x50);
  assert.equal(buf[2], 0x4e);
  assert.equal(buf[3], 0x47);
  assert.ok(buf.length > 100, `expected png larger than 100 bytes, got ${buf.length}`);
  fs.rmSync(file, { force: true });
});

test('renderTerminal produces a non-empty string', async () => {
  const out = await renderTerminal('hello');
  assert.ok(typeof out === 'string' && out.length > 0);
});