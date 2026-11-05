import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, before, test } from 'node:test';
import type { Account } from '../src/demo.js';
import { accounts, scenarios } from '../src/demo.js';
import type { Projection } from '../src/projection.js';
import { catchUp, readCheckpoint, rebuild, writeCheckpoint } from '../src/projection.js';
import { EventStore } from '../src/store.js';
import type { StoredEvent } from '../src/types.js';
import { StoreError } from '../src/types.js';

let directory = '';

before(() => {
  directory = mkdtempSync(join(tmpdir(), 'eso-projection-'));
});

after(() => {
  rmSync(directory, { recursive: true, force: true });
});

function seeded(name: string): EventStore {
  const store = EventStore.open(join(directory, name));
  store.append('a', 0, [{ type: 'deposited', data: { amount: 100 } }]);
  store.append('a', 1, [
    { type: 'withdrawn', data: { amount: 30 } },
    { type: 'deposited', data: { amount: 5 } },
  ]);
  return store;
}

test('a rebuild folds the whole log', () => {
  const applied = rebuild(seeded('rebuild.jsonl'), accounts);
  assert.equal(applied.applied, 3);
  assert.equal(applied.state.balance, 75);
  assert.equal(applied.state.deposits, 2);
  assert.equal(applied.state.withdrawals, 1);
  assert.deepEqual(applied.state.streams, ['a']);
});

test('a saved state plus its position resumes to the same place as a rebuild', () => {
  const store = EventStore.open(join(directory, 'resume.jsonl'));
  store.append('a', 0, [{ type: 'deposited', data: { amount: 100 } }]);
  const early = rebuild(store, accounts);
  assert.equal(early.position, 1);
  store.append('a', 1, [
    { type: 'withdrawn', data: { amount: 30 } },
    { type: 'deposited', data: { amount: 5 } },
  ]);
  const full = rebuild(store, accounts);
  const resumed = catchUp(store, accounts, early.state, early.position);
  assert.equal(resumed.applied, 2);
  assert.equal(resumed.skipped, 1);
  assert.deepEqual(resumed.state, full.state);
});

test('a position without its state under-folds, which is why both are saved', () => {
  const store = seeded('underfold.jsonl');
  const full = rebuild(store, accounts);
  const wrong = catchUp(store, accounts, accounts.initial, 2);
  assert.equal(wrong.applied, 1);
  assert.notDeepEqual(wrong.state, full.state);
  assert.equal(wrong.state.balance, 5, 'only the event after the checkpoint was folded in');
});

test('a checkpoint past the end of the log is refused', () => {
  const store = seeded('ahead.jsonl');
  assert.throws(() => catchUp(store, accounts, accounts.initial, 9), /belongs to a different log/);
});

test('catching up twice at the head applies nothing', () => {
  const store = seeded('idempotent.jsonl');
  const once = catchUp(store, accounts, accounts.initial, 0);
  const twice = catchUp(store, accounts, once.state, once.position);
  assert.equal(twice.applied, 0);
  assert.deepEqual(twice.state, once.state);
});

test('the checkpoint round-trips position and state', () => {
  const path = join(directory, 'accounts.checkpoint');
  const store = seeded('checkpoint.jsonl');
  const full = rebuild(store, accounts);
  writeCheckpoint(path, full.position, full.state);
  const saved = readCheckpoint<Account>(path);
  assert.equal(saved.position, 3);
  assert.deepEqual(saved.state, full.state);
  assert.deepEqual(readdirSync(directory).filter((name) => name.endsWith('.tmp')), []);
});

test('a missing checkpoint is position 0 with no state', () => {
  const saved = readCheckpoint<Account>(join(directory, 'absent.checkpoint'));
  assert.equal(saved.position, 0);
  assert.equal(saved.state, null);
});

test('a checkpoint without a position raises', () => {
  const path = join(directory, 'broken.checkpoint');
  writeFileSync(path, '{"state":{}}\n');
  assert.throws(() => readCheckpoint(path), StoreError);
  writeFileSync(path, 'not json');
  assert.throws(() => readCheckpoint(path), /not valid JSON/);
});

test('a negative checkpoint is refused on write', () => {
  assert.throws(() => writeCheckpoint(join(directory, 'neg.checkpoint'), -1, {}), StoreError);
});

test('an unknown event type is ignored but its stream is recorded', () => {
  const store = EventStore.open(join(directory, 'unknown.jsonl'));
  store.append('a', 0, [{ type: 'audited', data: { who: 'ops' } }]);
  const applied = rebuild(store, accounts);
  assert.equal(applied.state.balance, 0);
  assert.deepEqual(applied.state.streams, ['a']);
});

test('an overdraw is a fact, not an error', () => {
  const store = EventStore.open(join(directory, 'overdraw.jsonl'));
  store.append('a', 0, [{ type: 'withdrawn', data: { amount: 500 } }]);
  assert.equal(rebuild(store, accounts).state.balance, -500);
});

test('a projection sees its streams in stable order', () => {
  const store = EventStore.open(join(directory, 'order.jsonl'));
  store.append('zeta', 0, [{ type: 'deposited', data: { amount: 1 } }]);
  store.append('alpha', 0, [{ type: 'deposited', data: { amount: 1 } }]);
  assert.deepEqual(rebuild(store, accounts).state.streams, ['alpha', 'zeta']);
});

test('the demo catches up to the same state as a rebuild', () => {
  const stories = scenarios(join(directory, 'demo'));
  assert.equal(stories.length, 5);
  assert.ok(stories[1]?.lines.some((line) => line.includes('yes: the fold is replayable')));
  assert.match(stories[2]?.title ?? '', /does not double count/);
});

test('a projection that counts applications exposes a double fold', () => {
  const counting: Projection<{ n: number }> = {
    name: 'counting',
    initial: { n: 0 },
    apply(state: { n: number }, _event: StoredEvent) {
      return { n: state.n + 1 };
    },
  };
  const store = seeded('counting.jsonl');
  const once = catchUp(store, counting, counting.initial, 0);
  const twice = catchUp(store, counting, counting.initial, 0);
  assert.equal(once.state.n, 3);
  assert.equal(twice.state.n, 3);
  const resume = catchUp(store, counting, once.state, once.position);
  assert.equal(resume.state.n, 3, 'a resume must not re-fold the prefix');
});
