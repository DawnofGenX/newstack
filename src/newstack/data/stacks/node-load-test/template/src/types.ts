//! The two records every other module agrees on.

/** One attempt against the target.
 *
 * `dueAt` is when the request was allowed to start, not when the socket was free:
 * measuring from the moment a slot opens hides queueing delay, which is the single
 * most common way a load test reports a latency nobody experiences.
 */
export interface Sample {
  /** Position in the run, 0-based; ties warm-up samples to their order. */
  readonly index: number;
  /** Monotonic nanoseconds when the request became due. */
  readonly dueAt: bigint;
  /** Milliseconds from `dueAt` to the last response byte, queueing included. */
  readonly latencyMs: number;
  /** HTTP status, or 0 when the request never produced one. */
  readonly status: number;
  readonly ok: boolean;
  readonly error?: string;
}

export interface Threshold {
  readonly name: string;
  readonly limit: number;
}
