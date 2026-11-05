import { mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import type { Projection } from './projection.js';
import { catchUp, readCheckpoint, rebuild, writeCheckpoint } from './projection.js';
import { EventStore } from './store.js';
import type { StoredEvent } from './types.js';

export interface Account {
  balance: number;
  deposits: number;
  withdrawals: number;
  /** Streams seen, so two projections can be compared without trusting a total. */
  streams: string[];
}

export const accounts: Projection<Account> = {
  name: 'accounts',
  initial: { balance: 0, deposits: 0, withdrawals: 0, streams: [] },
  apply(state: Account, event: StoredEvent): Account {
    const amount = (event.data as { amount?: unknown }).amount;
    const streams = state.streams.includes(event.stream)
      ? state.streams
      : [...state.streams, event.stream].sort();
    if (typeof amount !== 'number') return { ...state, streams };
    if (event.type === 'deposited') {
      return { ...state, balance: state.balance + amount, deposits: state.deposits + 1, streams };
    }
    if (event.type === 'withdrawn') {
      // The event is a fact even when it overdraws: refusing it here would make
      // the projection disagree with the log, which is the one thing it may not do.
      return { ...state, balance: state.balance - amount, withdrawals: state.withdrawals + 1, streams };
    }
    return { ...state, streams };
  },
};

export interface Story {
  title: string;
  lines: string[];
}

export function scenarios(directory: string): Story[] {
  mkdirSync(directory, { recursive: true });
  const logPath = join(directory, 'events.jsonl');
  const checkpointPath = join(directory, 'accounts.checkpoint');
  for (const path of [logPath, checkpointPath]) rmSync(path, { force: true });

  const store = EventStore.open(logPath);
  store.append('account-42', 0, [{ type: 'deposited', data: { amount: 100 } }]);
  store.append('account-42', 1, [
    { type: 'withdrawn', data: { amount: 30 } },
    { type: 'deposited', data: { amount: 5 } },
  ]);
  store.append('account-7', 0, [{ type: 'deposited', data: { amount: 12.5 } }]);

  const stories: Story[] = [];

  const full = rebuild(store, accounts);
  stories.push({
    title: 'a rebuild reads every event',
    lines: [
      `events     ${store.position}`,
      `applied    ${full.applied}`,
      `balance    ${full.state.balance}`,
      `streams    ${full.state.streams.join(', ')}`,
    ],
  });

  const first = catchUp(store, accounts, accounts.initial, 0);
  writeCheckpoint(checkpointPath, first.position, first.state);
  const second = catchUp(store, accounts, first.state, readCheckpoint<Account>(checkpointPath).position);
  stories.push({
    title: 'catch-up equals rebuild',
    lines: [
      `first      ${first.applied} event(s), checkpoint ${readCheckpoint<Account>(checkpointPath).position}`,
      `second     ${second.applied} event(s) new, ${second.skipped} already folded in`,
      `same       ${JSON.stringify(second.state) === JSON.stringify(full.state) ? 'yes: the fold is replayable' : 'NO: the projection is not a function of the log'}`,
    ],
  });

  const stored = readCheckpoint<Account>(checkpointPath);
  const replayed = catchUp(store, accounts, stored.state ?? accounts.initial, stored.position);
  stories.push({
    title: 'a checkpoint read back from disk does not double count',
    lines: [
      `checkpoint ${stored.position} read back with its state`,
      `applied    ${replayed.applied} event(s); ${replayed.skipped} are already folded in`,
      `balance    ${replayed.state.balance} (a second fold would say ${replayed.state.balance * 2})`,
    ],
  });

  let refused = '';
  try {
    store.append('account-42', 1, [{ type: 'deposited', data: { amount: 999 } }]);
  } catch (error) {
    refused = (error as Error).message;
  }
  stories.push({
    title: 'a stale expected version is refused',
    lines: [
      `refused    ${refused}`,
      `balance    ${(rebuild(store, accounts).state as Account).balance} (the log did not move)`,
    ],
  });

  const reopened = EventStore.open(logPath);
  stories.push({
    title: 'reopening the file keeps every version',
    lines: [
      `events     ${reopened.position}`,
      `dropped    ${reopened.dropped} torn line(s)`,
      `account-42 ${reopened.version('account-42')}`,
      `balance    ${(rebuild(reopened, accounts).state as Account).balance}`,
    ],
  });

  return stories;
}
