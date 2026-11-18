import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createScheduler } from '../src/scheduler.js';

test('scheduler records repeated runs', { timeout: 10000 }, async () => {
  const storePath = path.join(os.tmpdir(), `cron-${Date.now()}.json`);
  const scheduler = createScheduler(storePath);
  scheduler.register('tick', '* * * * * *', () => {});
  scheduler.start('tick');
  await new Promise((resolve) => setTimeout(resolve, 2500));
  scheduler.stop('tick');
  const store = JSON.parse(fs.readFileSync(storePath, 'utf8'));
  assert.ok(store.jobs.tick.runs >= 2, `expected >=2 runs, got ${store.jobs.tick.runs}`);
  assert.equal(typeof store.jobs.tick.lastRun, 'string');
  fs.rmSync(storePath, { force: true });
});

test('scheduler records lastError when a job throws', { timeout: 10000 }, async () => {
  const storePath = path.join(os.tmpdir(), `cron-err-${Date.now()}.json`);
  const scheduler = createScheduler(storePath);
  scheduler.register('boom', '* * * * * *', () => { throw new Error('boom'); });
  scheduler.start('boom');
  await new Promise((resolve) => setTimeout(resolve, 1300));
  scheduler.stop('boom');
  const store = JSON.parse(fs.readFileSync(storePath, 'utf8'));
  assert.match(store.jobs.boom.lastError, /boom/);
  fs.rmSync(storePath, { force: true });
});