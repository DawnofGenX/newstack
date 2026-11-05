import { mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Account } from './demo.js';
import { scenarios } from './demo.js';
import { main } from './main.js';
import type { Projection } from './projection.js';
import { catchUp, readCheckpoint, rebuild, writeCheckpoint } from './projection.js';
import { EventStore } from './store.js';
import type { StoredEvent } from './types.js';
import { ConcurrencyError, StoreError } from './types.js';

let failures = 0;
let checks = 0;

function check(name: string, condition: boolean, detail = ''): void {
  checks += 1;
  if (condition) return;
  failures += 1;
  console.log(`FAIL ${name}${detail === '' ? '' : `: ${detail}`}`);
}

function throws(name: string, fn: () => unknown, kind: unknown): void {
  try {
    fn();
  } catch (error) {
    check(name, error instanceof (kind as new (...args: never[]) => Error), `got ${String(error)}`);
    return;
  }
  check(name, false, 'it did not throw');
}

function quiet<T>(fn: () => T): T {
  const write = process.stdout.write.bind(process.stdout);
  const error = console.error;
  const log = console.log;
  process.stdout.write = (() => true) as typeof process.stdout.write;
  console.error = () => undefined;
  console.log = () => undefined;
  try {
    return fn();
  } finally {
    process.stdout.write = write;
    console.error = error;
    console.log = log;
  }
}

export function selftest(): number {
  const directory = mkdtempSync(join(tmpdir(), 'eso-selftest-'));
  try {
    const log = join(directory, 'events.jsonl');
    const store = EventStore.open(log);

    const first = store.append('a', 0, [{ type: 'deposited', data: { amount: 10 } }]);
    check('the first append starts at version 1', first.fromVersion === 1 && first.toVersion === 1);
    check('positions start at 0', first.events[0]?.position === 0);
    check('version() follows the appends', store.version('a') === 1);
    check('an unknown stream is at version 0', store.version('nobody') === 0);

    const second = store.append('a', 1, [
      { type: 'withdrawn', data: { amount: 3 } },
      { type: 'deposited', data: { amount: 2 } },
    ]);
    check('a batch numbers its events consecutively', second.fromVersion === 2 && second.toVersion === 3);
    check('a batch takes consecutive positions', second.events.map((e) => e.position).join(',') === '1,2');
    check('the log position counts events', store.position === 3);

    throws(
      'a stale expected version is refused',
      () => store.append('a', 1, [{ type: 'deposited', data: { amount: 1 } }]),
      ConcurrencyError,
    );
    try {
      store.append('a', 1, [{ type: 'deposited', data: { amount: 1 } }]);
    } catch (error) {
      check(
        'the refusal names the expected and the actual version',
        (error as Error).message.includes('version 3, not 1'),
        (error as Error).message,
      );
      check(
        'the refusal says what to do about it',
        (error as Error).message.includes('re-reading before retrying'),
        (error as Error).message,
      );
    }
    check('a refused append does not move the version', store.version('a') === 3);

    throws('an empty append is refused', () => store.append('a', 3, []), StoreError);
    throws('an empty stream name is refused', () => store.append('  ', 0, [{ type: 'x', data: {} }]), StoreError);
    throws('a stream name with a slash is refused', () => store.append('a/b', 0, [{ type: 'x', data: {} }]), StoreError);
    throws('an event without a type is refused', () => store.append('b', 0, [{ type: '', data: {} }]), StoreError);

    const lines = readFileSync(log, 'utf8').split('\n').filter((line) => line !== '');
    check('one append is one line', lines.length === 2, `${lines.length} line(s) for 2 append(s)`);

    const reopened = EventStore.open(log);
    check('reopening keeps the position', reopened.position === 3);
    check('reopening keeps the version', reopened.version('a') === 3);
    check('reopening drops nothing', reopened.dropped === 0);
    check('readStream starts where asked', reopened.readStream('a', 3).length === 1);
    check('readAll starts where asked', reopened.readAll(2).length === 1);
    check('streams() is sorted', reopened.streams().join(',') === 'a');

    const full = rebuild(reopened, accountProjection);
    check('a rebuild folds every event', full.applied === 3);
    check('the rebuild lands at the log position', full.position === 3);

    const step = catchUp(reopened, accountProjection, accountProjection.initial, 2);
    check('catch-up applies only the tail', step.applied === 1);
    check('catch-up reports what it skipped', step.skipped === 2);
    const again = catchUp(reopened, accountProjection, step.state, step.position);
    check('catch-up at the head applies nothing', again.applied === 0);
    check(
      'catch-up is idempotent',
      JSON.stringify(again.state) === JSON.stringify(step.state),
      JSON.stringify(again.state),
    );

    const checkpoint = join(directory, 'accounts.checkpoint');
    writeCheckpoint(checkpoint, full.position, full.state);
    const saved = readCheckpoint<typeof full.state>(checkpoint);
    check('the checkpoint keeps its position', saved.position === 3);
    check(
      'the checkpoint keeps its state',
      JSON.stringify(saved.state) === JSON.stringify(full.state),
    );
    check('no temporary checkpoint is left behind', !readdirHas(directory, 'accounts.checkpoint.tmp'));
    const resumed = catchUp(reopened, accountProjection, saved.state ?? accountProjection.initial, saved.position);
    check('a resume at the head changes nothing', resumed.applied === 0);

    const torn = join(directory, 'torn.jsonl');
    writeFileSync(torn, `${lines[0]}\n{"stream":"a","fromVers`);
    const salvaged = EventStore.open(torn);
    check('a torn final line is dropped', salvaged.dropped === 1);
    check('the events before it survive', salvaged.position === 1);

    const damaged = join(directory, 'damaged.jsonl');
    writeFileSync(damaged, `{"stream":\n${lines[0]}\n`);
    throws('a damaged line inside the log raises', () => EventStore.open(damaged), StoreError);

    const holed = join(directory, 'holed.jsonl');
    writeFileSync(
      holed,
      `${JSON.stringify({ stream: 'a', fromVersion: 2, toVersion: 2, at: 'x', events: [{ type: 't', data: {} }] })}\n`,
    );
    throws('a version hole raises', () => EventStore.open(holed), StoreError);

    const batchLog = join(directory, 'batch.jsonl');
    const batchStore = EventStore.open(batchLog);
    batchStore.append('s', 0, [
      { type: 'deposited', data: { amount: 1 } },
      { type: 'deposited', data: { amount: 2 } },
    ]);
    const stored = JSON.parse(readFileSync(batchLog, 'utf8').trim()) as { events: unknown[] };
    check('a batch is stored as one record', stored.events.length === 2);
    check('the batch line is a single line', readFileSync(batchLog, 'utf8').trim().split('\n').length === 1);

    const stories = scenarios(join(directory, 'demo'));
    check('the demo tells five stories', stories.length === 5, `${stories.length}`);
    check(
      'the demo proves catch-up equals rebuild',
      stories[1]?.lines.some((line) => line.includes('yes: the fold is replayable')) ?? false,
    );
    check(
      'the demo refuses a stale append',
      stories[3]?.lines.some((line) => line.includes('re-reading before retrying')) ?? false,
    );

    const cliLog = join(directory, 'cli.jsonl');
    check(
      'the cli appends',
      quiet(() =>
        main([
          'append', '--log', cliLog, '--stream', 'acct', '--expected-version', '0',
          '--type', 'deposited', '--data', '{"amount":7}',
        ]),
      ) === 0,
    );
    check(
      'the cli refuses a stale append with exit 1',
      quiet(() =>
        main([
          'append', '--log', cliLog, '--stream', 'acct', '--expected-version', '0',
          '--type', 'deposited', '--data', '{"amount":7}',
        ]),
      ) === 1,
    );
    check(
      'the cli rejects malformed json with exit 2',
      quiet(() =>
        main([
          'append', '--log', cliLog, '--stream', 'acct', '--expected-version', '1',
          '--type', 'deposited', '--data', '{oops',
        ]),
      ) === 2,
    );
    check('the cli rejects an unknown command with exit 2', quiet(() => main(['nope'])) === 2);
    check('the cli prints its version', quiet(() => main(['--version'])) === 0);
    const checkpointPath = join(directory, 'cli.checkpoint');
    check(
      'the cli projects',
      quiet(() => main(['project', '--log', cliLog, '--checkpoint', checkpointPath])) === 0,
    );
    check('the cli wrote a checkpoint', readCheckpoint(checkpointPath).position === 1);
    check(
      'projecting twice is stable',
      quiet(() => main(['project', '--log', cliLog, '--checkpoint', checkpointPath])) === 0,
    );
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }

  if (failures === 0) {
    console.log(`selftest: ${checks} checks passed`);
    return 0;
  }
  console.log(`selftest: ${failures} of ${checks} checks failed`);
  return 1;
}

function readdirHas(directory: string, name: string): boolean {
  return readdirSync(directory).includes(name);
}

const accountProjection: Projection<Account> = {
  name: 'selftest-accounts',
  initial: { balance: 0, deposits: 0, withdrawals: 0, streams: [] },
  apply(state: Account, event: StoredEvent): Account {
    const amount = (event.data as { amount?: unknown }).amount;
    const streams = state.streams.includes(event.stream)
      ? state.streams
      : [...state.streams, event.stream].sort();
    if (typeof amount !== 'number') return { ...state, streams };
    return event.type === 'deposited'
      ? { ...state, balance: state.balance + amount, deposits: state.deposits + 1, streams }
      : { ...state, balance: state.balance - amount, withdrawals: state.withdrawals + 1, streams };
  },
};

if (process.argv[1] !== undefined && fileURLToPath(import.meta.url) === process.argv[1]) {
  process.exitCode = selftest();
}
