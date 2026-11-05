export interface EventInput {
  type: string;
  data: unknown;
}

export interface StoredEvent {
  /** The stream the event belongs to, e.g. `account-42`. */
  stream: string;
  /** 1-based position within the stream. Never reused, never skipped. */
  version: number;
  /** 0-based position in the whole log: the only total order the store has. */
  position: number;
  type: string;
  at: string;
  data: unknown;
}

export interface Batch {
  stream: string;
  fromVersion: number;
  toVersion: number;
  at: string;
  events: EventInput[];
}

export interface AppendResult {
  stream: string;
  fromVersion: number;
  toVersion: number;
  events: StoredEvent[];
}

export class StoreError extends Error {}

/** The store refused an append because somebody else wrote first. */
export class ConcurrencyError extends StoreError {
  constructor(
    readonly stream: string,
    readonly expected: number,
    readonly actual: number,
  ) {
    super(
      `stream ${stream} is at version ${actual}, not ${expected}: ` +
        'another writer appended first, and re-reading before retrying is the only safe answer',
    );
    this.name = 'ConcurrencyError';
  }
}

export function validateStream(stream: string): void {
  if (stream.trim() === '') {
    throw new StoreError('a stream name cannot be empty');
  }
  if (stream.includes('/')) {
    throw new StoreError(`stream ${stream} cannot contain '/'`);
  }
}

export function validateBatch(events: readonly EventInput[]): void {
  if (events.length === 0) {
    throw new StoreError('an append needs at least one event');
  }
  for (const event of events) {
    if (event.type.trim() === '') {
      throw new StoreError('an event needs a type');
    }
  }
}
