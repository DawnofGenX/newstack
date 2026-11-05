import { Worker } from "node:worker_threads";

import type { CloseReport, Job, JobResult, JobKind, PoolStats } from "./types.js";

export class PoolError extends Error {}

export interface PoolOptions {
  readonly size?: number;
  readonly maxQueue?: number;
  readonly workerUrl?: URL;
}

interface Pending {
  readonly job: Job;
  readonly resolve: (value: unknown) => void;
  readonly reject: (error: Error) => void;
  readonly transfer: ArrayBuffer[];
}

interface Slot {
  readonly worker: Worker;
  job: Job | null;
  resolve: ((value: unknown) => void) | null;
  reject: ((error: Error) => void) | null;
}

const DEFAULT_WORKER = new URL("./worker.js", import.meta.url);

/**
 * A fixed-size pool of worker threads with a bounded queue.
 *
 * Three things this class refuses to do: grow the queue past `maxQueue`, report a crashed
 * worker as a task that simply never finished, and copy a buffer it was asked to transfer.
 */
export class Pool {
  readonly size: number;
  readonly maxQueue: number;
  readonly #workerUrl: URL;
  readonly #slots: Slot[] = [];
  readonly #idle: Slot[] = [];
  readonly #queue: Pending[] = [];
  #closing = false;
  #nextId = 1;
  #spawns = 0;
  #completed = 0;
  #failed = 0;
  #replaced = 0;
  #refused = 0;
  #peakQueue = 0;

  constructor(options: PoolOptions = {}) {
    this.size = options.size ?? 4;
    this.maxQueue = options.maxQueue ?? 1024;
    this.#workerUrl = options.workerUrl ?? DEFAULT_WORKER;
    if (!Number.isInteger(this.size) || this.size < 1) {
      throw new PoolError(`size must be an integer >= 1, got ${this.size}`);
    }
    if (!Number.isInteger(this.maxQueue) || this.maxQueue < 0) {
      throw new PoolError(`maxQueue must be an integer >= 0, got ${this.maxQueue}`);
    }
  }

  /** Spawn one worker now instead of waiting for the first job. */
  async warm(): Promise<void> {
    while (this.#slots.length < this.size) {
      const slot = this.#spawn();
      await new Promise<void>((resolve) => {
        slot.worker.once("online", () => {
          resolve();
        });
      });
      this.#idle.push(slot);
    }
  }

  run<T = unknown>(kind: JobKind, payload: Partial<Job> = {}, transfer: ArrayBuffer[] = []): Promise<T> {
    if (this.#closing) {
      return Promise.reject(new PoolError("the pool is closing and accepts no new work"));
    }
    const queued = this.#queue.length;
    if (queued >= this.maxQueue) {
      this.#refused += 1;
      return Promise.reject(
        new PoolError(
          `the queue holds ${queued} task(s), which is the maxQueue limit; ` +
            "refusing the task keeps the backlog a bound rather than a leak",
        ),
      );
    }
    const job: Job = { ...payload, id: this.#nextId, kind };
    this.#nextId += 1;
    return new Promise<T>((resolve, reject) => {
      const pending: Pending = {
        job,
        resolve: resolve as (value: unknown) => void,
        reject,
        transfer,
      };
      const slot = this.#idle.pop();
      if (slot !== undefined) {
        this.#dispatch(slot, pending);
        return;
      }
      if (this.#slots.length < this.size) {
        this.#dispatch(this.#spawn(), pending);
        return;
      }
      this.#queue.push(pending);
      this.#peakQueue = Math.max(this.#peakQueue, this.#queue.length);
    });
  }

  stats(): PoolStats {
    const busy = this.#slots.filter((slot) => slot.job !== null).length;
    return {
      size: this.size,
      spawns: this.#spawns,
      completed: this.#completed,
      failed: this.#failed,
      replaced: this.#replaced,
      queued: this.#queue.length,
      peakQueue: this.#peakQueue,
      busy,
      idle: this.#slots.length - busy,
    };
  }

  /** Resolve when nothing is queued and every worker is idle. */
  async drained(): Promise<void> {
    while (this.#queue.length > 0 || this.#slots.some((slot) => slot.job !== null)) {
      await new Promise((resolve) => setTimeout(resolve, 5));
    }
  }

  /** Stop accepting work, let the backlog finish, then exit every worker. */
  async close(): Promise<CloseReport> {
    this.#closing = true;
    await this.drained();
    await Promise.all(
      this.#slots.map(async (slot) => {
        await slot.worker.terminate();
      }),
    );
    this.#slots.length = 0;
    this.#idle.length = 0;
    return {
      completed: this.#completed,
      failed: this.#failed,
      refused: this.#refused,
      spawns: this.#spawns,
      replaced: this.#replaced,
    };
  }

  #spawn(): Slot {
    this.#spawns += 1;
    const worker = new Worker(this.#workerUrl);
    const slot: Slot = { worker, job: null, resolve: null, reject: null };
    this.#slots.push(slot);
    worker.on("message", (message: JobResult) => {
      this.#settle(slot, message);
    });
    worker.on("error", (error: Error) => {
      this.#lose(slot, error);
    });
    worker.on("exit", (code: number) => {
      // A worker that exits while holding a job took that job with it. Reporting "exited"
      // is the only honest answer: the task did not fail with a result, it stopped existing.
      this.#lose(slot, new Error(`the worker exited with code ${code} before answering`));
    });
    return slot;
  }

  #dispatch(slot: Slot, pending: Pending): void {
    slot.job = pending.job;
    slot.resolve = pending.resolve;
    slot.reject = pending.reject;
    // The transfer list travels with the task: a queued task that is dispatched later must
    // still move its buffer rather than clone a megabyte at dispatch time.
    slot.worker.postMessage(pending.job, pending.transfer);
  }

  #settle(slot: Slot, message: JobResult): void {
    if (slot.job === null || message.id !== slot.job.id) {
      // A late answer for a job that was already rejected: it must not resolve anyone.
      return;
    }
    const resolve = slot.resolve;
    const reject = slot.reject;
    slot.job = null;
    slot.resolve = null;
    slot.reject = null;
    if (message.ok) {
      this.#completed += 1;
      resolve?.(message.buffer === undefined ? message.value : { value: message.value, buffer: message.buffer });
    } else {
      this.#failed += 1;
      const remote = message.error;
      const error = new Error(remote?.message ?? "the worker failed without a message");
      error.name = remote?.name ?? "Error";
      error.stack = `${error.name}: ${error.message}\n    at the worker thread\n${remote?.stack ?? ""}`;
      reject?.(error);
    }
    this.#release(slot);
  }

  #release(slot: Slot): void {
    const next = this.#queue.shift();
    if (next === undefined) {
      if (!this.#idle.includes(slot)) this.#idle.push(slot);
      return;
    }
    this.#dispatch(slot, next);
  }

  #lose(slot: Slot, error: Error): void {
    const reject = slot.reject;
    const had = slot.job !== null;
    slot.job = null;
    slot.resolve = null;
    slot.reject = null;
    if (had) {
      this.#failed += 1;
      reject?.(error);
    }
    const at = this.#slots.indexOf(slot);
    if (at >= 0) this.#slots.splice(at, 1);
    const idleAt = this.#idle.indexOf(slot);
    if (idleAt >= 0) this.#idle.splice(idleAt, 1);
    if (this.#closing) return;
    this.#replaced += 1;
    // Replace only if there is work the pool would otherwise swallow.
    const wanted = Math.min(this.size, this.#slots.length + this.#queue.length + (had ? 1 : 0));
    while (this.#slots.length < wanted) {
      const fresh = this.#spawn();
      const next = this.#queue.shift();
      if (next === undefined) {
        this.#idle.push(fresh);
        break;
      }
      this.#dispatch(fresh, next);
    }
  }
}
