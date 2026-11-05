import { readFileSync, renameSync, writeFileSync } from 'node:fs';
import type { EventStore } from './store.js';
import type { StoredEvent } from './types.js';
import { StoreError } from './types.js';

/**
 * A projection is a fold over the log. `apply` must be a pure function of
 * (state, event): the same log replayed twice must produce the same state, and
 * replaying a *prefix* must land exactly where an incremental run left off.
 *
 * The checkpoint is a position, not a count and not a version. Positions are
 * global, so one number covers every stream the projection reads; a per-stream
 * version would need a tuple per stream and would still be ambiguous the moment
 * a batch spans two streams.
 */
export interface Projection<S> {
  name: string;
  initial: S;
  apply(state: S, event: StoredEvent): S;
}

export interface Applied<S> {
  state: S;
  /** Position after the last event applied; equal to the checkpoint when nothing was. */
  position: number;
  applied: number;
  /** Events handed over that the checkpoint said were already folded in. */
  skipped: number;
  events: StoredEvent[];
}

export function catchUp<S>(
  store: EventStore,
  projection: Projection<S>,
  state: S,
  checkpoint: number,
): Applied<S> {
  if (!Number.isInteger(checkpoint) || checkpoint < 0) {
    throw new StoreError(`checkpoint must be an integer >= 0, got ${checkpoint}`);
  }
  if (checkpoint > store.position) {
    // A checkpoint past the end is not "nothing to do": it belongs to another
    // log, and resuming from it would leave events permanently unprojected.
    throw new StoreError(
      `checkpoint ${checkpoint} is ahead of the log position ${store.position}: ` +
        'this checkpoint belongs to a different log',
    );
  }
  const history = store.readAll(checkpoint);
  let current = state;
  let position = checkpoint;
  let applied = 0;
  for (const event of history) {
    current = projection.apply(current, event);
    position = event.position + 1;
    applied += 1;
  }
  // Everything before the checkpoint is already folded into `state`.
  return { state: current, position, applied, skipped: checkpoint, events: history };
}

export function rebuild<S>(store: EventStore, projection: Projection<S>): Applied<S> {
  return catchUp(store, projection, projection.initial, 0);
}

export interface Checkpoint<S> {
  position: number;
  /** The folded state at `position`; `null` when the checkpoint only remembers how far it got. */
  state: S | null;
}

export function readCheckpoint<S>(path: string): Checkpoint<S> {
  let text: string;
  try {
    text = readFileSync(path, 'utf8');
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return { position: 0, state: null };
    throw error;
  }
  let payload: unknown;
  try {
    payload = JSON.parse(text);
  } catch (error) {
    throw new StoreError(`${path}: checkpoint is not valid JSON: ${(error as Error).message}`);
  }
  const record = payload as { position?: unknown; state?: unknown };
  const position = record.position;
  if (typeof position !== 'number' || !Number.isInteger(position) || position < 0) {
    throw new StoreError(`${path}: checkpoint has no integer position`);
  }
  return { position, state: (record.state ?? null) as S | null };
}

/**
 * Write the checkpoint atomically: a checkpoint saved after the state it
 * describes, or not at all, but never half way. The position and the state go
 * into the same file so a resume can never pair one run's position with
 * another run's state.
 */
export function writeCheckpoint<S>(path: string, position: number, state: S): void {
  if (!Number.isInteger(position) || position < 0) {
    throw new StoreError(`refusing to write checkpoint ${position}`);
  }
  const temporary = `${path}.tmp`;
  writeFileSync(temporary, `${JSON.stringify({ position, state })}\n`);
  renameSync(temporary, path);
}
