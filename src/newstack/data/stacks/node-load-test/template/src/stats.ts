//! Percentiles, with the algorithm spelled out.

import type { Sample } from "./types.js";

export interface Summary {
  /** Named so a number in a report can always be reproduced by hand. */
  readonly method: "nearest-rank";
  /** Samples that were measured (warm-up excluded). */
  readonly count: number;
  /** Samples dropped as warm-up. */
  readonly warmup: number;
  readonly errors: number;
  readonly errorRate: number;
  readonly min: number;
  readonly p50: number;
  readonly p90: number;
  readonly p95: number;
  readonly p99: number;
  readonly max: number;
  readonly mean: number;
  /** Status codes seen, so a 503 near the end is not just "some errors". */
  readonly statuses: Record<string, number>;
}

/** The p-th percentile, nearest-rank: the smallest value whose rank covers p%.
 *
 * Nearest-rank is used because every answer it gives is a latency that actually
 * happened. Linear interpolation between neighbours invents values: p95 of
 * 1..100 is 95 here and 95.05 there, and only one of those numbers can be
 * checked against a trace.
 */
export function percentile(values: readonly number[], p: number): number {
  if (!(p > 0 && p <= 100)) {
    throw new RangeError(`percentile must be in (0, 100], got ${p}`);
  }
  if (values.length === 0) {
    throw new RangeError("percentile of an empty sample");
  }
  const sorted = [...values].sort((a, b) => a - b);
  const rank = Math.max(1, Math.ceil((p / 100) * sorted.length));
  return sorted[rank - 1] as number;
}

function meanOf(values: readonly number[]): number {
  let total = 0;
  for (const value of values) total += value;
  return total / values.length;
}

function round(value: number): number {
  return Math.round(value * 1000) / 1000;
}

/** Summarise a run, dropping the first `warmup` samples by index. */
export function summarize(samples: readonly Sample[], warmup = 0): Summary {
  if (warmup < 0) throw new RangeError(`warmup must be >= 0, got ${warmup}`);
  const ordered = [...samples].sort((a, b) => a.index - b.index);
  const measured = ordered.slice(warmup);
  if (measured.length === 0) {
    throw new RangeError(
      `no measured samples: ${warmup} of ${ordered.length} were dropped as warm-up`,
    );
  }
  const latencies = measured.map((sample) => sample.latencyMs);
  const errors = measured.filter((sample) => !sample.ok).length;
  const statuses: Record<string, number> = {};
  for (const sample of measured) {
    // A 503 keeps its code; only requests that never got a status are "error".
    const key = sample.status > 0 ? String(sample.status) : "error";
    statuses[key] = (statuses[key] ?? 0) + 1;
  }
  return {
    method: "nearest-rank",
    count: measured.length,
    warmup,
    errors,
    errorRate: round(errors / measured.length),
    min: round(Math.min(...latencies)),
    p50: round(percentile(latencies, 50)),
    p90: round(percentile(latencies, 90)),
    p95: round(percentile(latencies, 95)),
    p99: round(percentile(latencies, 99)),
    max: round(Math.max(...latencies)),
    mean: round(meanOf(latencies)),
    statuses,
  };
}
