import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, before, test } from 'node:test';
import { EventStore } from '../src/store.js';
import { ConcurrencyError, StoreError } from '../src/types.js';

let directory = '';

before(() => {
  directory = mkdtempSync(join(tmpdir(), 'eso-store-'));
});

after(() => {
  rmSync(directory, { recursive: true, force: true });
});

test('an append numbers versions from 1 and positions from 0', () => {
  const store = EventStore.open(join(directory, 'basic.jsonl'));
  const result = store.append('a', 0, [{ type: 'deposited', data: { amount: 1 } }]);
  assert.equal(result.fromVersion, 1);
  assert.equal(result.toVersion, 1);
  assert.equal(result.events[0]?.position, 0);
  assert.equal(result.events[0]?.version, 1);
});

test('a batch appends every event in one record', () => {
  const path = join(directory, 'batch.jsonl');
  const store = EventStore.open(path);
  store.append('a', 0, [
    { type: 'deposited', data: { amount: 1 } },
    { type: 'withdrawn', data: { amount: 1 } },
  ]);
  const lines = readFileSync(path, 'utf8').trim().split('\n');
  assert.equal(lines.length, 1);
  const record = JSON.parse(lines[0] as string) as { events: unknown[] };
  assert.equal(record.events.length, 2);
  assert.equal(store.position, 2);
});

test('a stale expected version raises ConcurrencyError', () => {
  const store = EventStore.open(join(directory, 'conflict.jsonl'));
  store.append('a', 0, [{ type: 'x', data: {} }]);
  store.append('a', 1, [{ type: 'x', data: {} }]);
  assert.throws(
    () => store.append('a', 1, [{ type: 'x', data: {} }]),
    (error: unknown) => {
      assert.ok(error instanceof ConcurrencyError);
      assert.equal(error.expected, 1);
      assert.equal(error.actual, 2);
      assert.match(error.message, /stream a is at version 2, not 1/);
      assert.match(error.message, /re-reading before retrying/);
      return true;
    },
  );
  assert.equal(store.version('a'), 2);
});

test('an append ahead of the stream is refused too', () => {
  const store = EventStore.open(join(directory, 'ahead.jsonl'));
  assert.throws(() => store.append('a', 5, [{ type: 'x', data: {} }]), ConcurrencyError);
});

test('an empty append, empty stream and typeless event are refused', () => {
  const store = EventStore.open(join(directory, 'refuse.jsonl'));
  assert.throws(() => store.append('a', 0, []), StoreError);
  assert.throws(() => store.append('', 0, [{ type: 'x', data: {} }]), StoreError);
  assert.throws(() => store.append('a/b', 0, [{ type: 'x', data: {} }]), StoreError);
  assert.throws(() => store.append('a', 0, [{ type: ' ', data: {} }]), StoreError);
  assert.throws(() => store.append('a', -1, [{ type: 'x', data: {} }]), StoreError);
});

test('reopening the log restores versions and positions', () => {
  const path = join(directory, 'reopen.jsonl');
  const store = EventStore.open(path);
  store.append('a', 0, [{ type: 'x', data: {} }]);
  store.append('b', 0, [{ type: 'x', data: {} }, { type: 'x', data: {} }]);
  const reopened = EventStore.open(path);
  assert.equal(reopened.position, 3);
  assert.equal(reopened.version('a'), 1);
  assert.equal(reopened.version('b'), 2);
  assert.deepEqual(reopened.streams(), ['a', 'b']);
  assert.equal(reopened.dropped, 0);
});

test('a torn final line is dropped and counted', () => {
  const path = join(directory, 'torn.jsonl');
  const store = EventStore.open(path);
  store.append('a', 0, [{ type: 'x', data: {} }]);
  writeFileSync(path, `${readFileSync(path, 'utf8')}{"stream":"a","fromVers`);
  const reopened = EventStore.open(path);
  assert.equal(reopened.dropped, 1);
  assert.equal(reopened.position, 1);
  assert.equal(reopened.version('a'), 1);
});

test('a damaged line before the end raises instead of renumbering history', () => {
  const path = join(directory, 'damaged.jsonl');
  const store = EventStore.open(path);
  store.append('a', 0, [{ type: 'x', data: {} }]);
  store.append('a', 1, [{ type: 'x', data: {} }]);
  const [first, second] = readFileSync(path, 'utf8').trim().split('\n');
  writeFileSync(path, `{"stream":\n${first}\n${second}\n`);
  assert.throws(() => EventStore.open(path), (error: unknown) => {
    assert.ok(error instanceof StoreError);
    assert.match((error as Error).message, /line 1 is not valid JSON/);
    return true;
  });
});

test('a version hole raises', () => {
  const path = join(directory, 'hole.jsonl');
  writeFileSync(
    path,
    `${JSON.stringify({ stream: 'a', fromVersion: 2, toVersion: 2, at: 'x', events: [{ type: 't', data: {} }] })}\n`,
  );
  assert.throws(() => EventStore.open(path), /versions have a hole/);
});

test('a batch whose range disagrees with its events raises', () => {
  const path = join(directory, 'range.jsonl');
  writeFileSync(
    path,
    `${JSON.stringify({ stream: 'a', fromVersion: 1, toVersion: 5, at: 'x', events: [{ type: 't', data: {} }] })}\n`,
  );
  assert.throws(() => EventStore.open(path), /claims 1\.\.5/);
});

test('reads honour the from argument', () => {
  const store = EventStore.open(join(directory, 'reads.jsonl'));
  store.append('a', 0, [{ type: 'x', data: {} }, { type: 'y', data: {} }, { type: 'z', data: {} }]);
  assert.equal(store.readStream('a').length, 3);
  assert.equal(store.readStream('a', 2).length, 2);
  assert.equal(store.readAll(2).length, 1);
  assert.equal(store.readStream('b').length, 0);
});
