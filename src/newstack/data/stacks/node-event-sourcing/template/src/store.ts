import { closeSync, fsyncSync, openSync, readFileSync, writeSync } from 'node:fs';
import type { AppendResult, Batch, EventInput, StoredEvent } from './types.js';
import { ConcurrencyError, StoreError, validateBatch, validateStream } from './types.js';

/**
 * An append-only log of events, one JSON object per line, one line per append.
 *
 * The two properties worth defending:
 *
 * 1. **An append is atomic.** Every event in one `append()` call goes into a
 *    single line and a single `writeSync` + `fsyncSync`, so a crash either
 *    records the whole batch or none of it. A per-event write would let a crash
 *    leave half a business fact behind, which no projection can interpret.
 * 2. **A torn final line is dropped, and counted.** A process that dies
 *    mid-write leaves a partial line; the loader ignores it and reports how many
 *    it ignored. A torn line anywhere else means the file was truncated or
 *    edited, and that raises instead of silently renumbering history.
 *
 * Versions are per stream and 1-based; positions are global and 0-based, so a
 * projection's checkpoint is a position and a retry guard is a version.
 */
export class EventStore {
  private batches: Batch[] = [];
  private events: StoredEvent[] = [];
  private versions = new Map<string, number>();
  private droppedLines = 0;

  private constructor(readonly path: string) {}

  static open(path: string): EventStore {
    const store = new EventStore(path);
    store.load();
    return store;
  }

  private load(): void {
    let text: string;
    try {
      text = readFileSync(this.path, 'utf8');
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (code === 'ENOENT') return;
      throw error;
    }
    const lines = text.split('\n');
    // A trailing newline produces an empty last element, which is not a torn line.
    if (lines.length > 0 && lines[lines.length - 1] === '') lines.pop();
    lines.forEach((line, index) => {
      if (line.trim() === '') return;
      let batch: Batch;
      try {
        batch = JSON.parse(line) as Batch;
      } catch (error) {
        if (index === lines.length - 1) {
          this.droppedLines += 1;
          return;
        }
        throw new StoreError(
          `${this.path}: line ${index + 1} is not valid JSON (${(error as Error).message}); ` +
            'a torn line inside the log means records were lost, and guessing which ones ' +
            'would invent history',
        );
      }
      this.applyBatch(batch, index + 1);
    });
  }

  private applyBatch(batch: Batch, line: number): void {
    if (typeof batch.stream !== 'string' || !Array.isArray(batch.events)) {
      throw new StoreError(`${this.path}: line ${line} is not an append record`);
    }
    const current = this.versions.get(batch.stream) ?? 0;
    if (batch.fromVersion !== current + 1) {
      throw new StoreError(
        `${this.path}: line ${line} starts ${batch.stream} at version ${batch.fromVersion} ` +
          `but the log is at ${current}; the versions have a hole`,
      );
    }
    if (batch.toVersion !== batch.fromVersion + batch.events.length - 1) {
      throw new StoreError(
        `${this.path}: line ${line} claims ${batch.fromVersion}..${batch.toVersion} ` +
          `for ${batch.events.length} event(s)`,
      );
    }
    const at = typeof batch.at === 'string' ? batch.at : new Date(0).toISOString();
    batch.events.forEach((event, offset) => {
      const stored: StoredEvent = {
        stream: batch.stream,
        version: batch.fromVersion + offset,
        position: this.events.length,
        type: event.type,
        at,
        data: event.data,
      };
      this.events.push(stored);
    });
    this.versions.set(batch.stream, batch.toVersion);
    this.batches.push(batch);
  }

  get dropped(): number {
    return this.droppedLines;
  }

  get position(): number {
    return this.events.length;
  }

  version(stream: string): number {
    return this.versions.get(stream) ?? 0;
  }

  streams(): string[] {
    return [...this.versions.keys()].sort();
  }

  readStream(stream: string, fromVersion = 1): StoredEvent[] {
    return this.events.filter(
      (event) => event.stream === stream && event.version >= fromVersion,
    );
  }

  readAll(fromPosition = 0): StoredEvent[] {
    return this.events.filter((event) => event.position >= fromPosition);
  }

  append(stream: string, expectedVersion: number, events: readonly EventInput[]): AppendResult {
    validateStream(stream);
    validateBatch(events);
    if (!Number.isInteger(expectedVersion) || expectedVersion < 0) {
      throw new StoreError(`expected version must be an integer >= 0, got ${expectedVersion}`);
    }
    const current = this.version(stream);
    if (current !== expectedVersion) {
      throw new ConcurrencyError(stream, expectedVersion, current);
    }
    const at = new Date().toISOString();
    const batch: Batch = {
      stream,
      fromVersion: current + 1,
      toVersion: current + events.length,
      at,
      events: events.map((event) => ({ type: event.type, data: event.data })),
    };
    const line = `${JSON.stringify(batch)}\n`;
    const handle = openSync(this.path, 'a');
    try {
      writeSync(handle, line);
      fsyncSync(handle);
    } finally {
      closeSync(handle);
    }
    this.applyBatch(batch, this.batches.length + 1);
    const appended = this.events.filter(
      (event) => event.stream === stream && event.version >= batch.fromVersion,
    );
    return {
      stream,
      fromVersion: batch.fromVersion,
      toVersion: batch.toVersion,
      events: appended,
    };
  }
}
