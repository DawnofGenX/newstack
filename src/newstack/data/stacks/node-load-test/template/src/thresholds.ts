//! Threshold parsing and evaluation: the part that lets a load test fail a build.

import type { Summary } from "./stats.js";
import type { Threshold } from "./types.js";

export const NAMES = ["p50", "p90", "p95", "p99", "max", "mean", "errorRate"] as const;

export type ThresholdName = (typeof NAMES)[number];

export function isThresholdName(value: string): value is ThresholdName {
  return (NAMES as readonly string[]).includes(value);
}

/** Parse `name=value` pairs.
 *
 * An unknown name is an error rather than a no-op: `--threshold p9=250` is a typo,
 * and a typo that silently passes is worse than no gate at all.
 */
export function parseThresholds(values: readonly string[]): Threshold[] {
  return values.map((raw) => {
    const at = raw.indexOf("=");
    if (at <= 0) throw new Error(`expected name=value, got ${JSON.stringify(raw)}`);
    const name = raw.slice(0, at);
    const text = raw.slice(at + 1);
    if (!isThresholdName(name)) {
      throw new Error(`unknown threshold ${JSON.stringify(name)}; choose one of ${NAMES.join(", ")}`);
    }
    const limit = Number(text);
    if (!Number.isFinite(limit) || limit < 0) {
      throw new Error(`threshold ${name} needs a non-negative number, got ${JSON.stringify(text)}`);
    }
    return { name, limit };
  });
}

export function measure(summary: Summary, name: ThresholdName): number {
  return summary[name];
}

export interface Verdict {
  readonly name: ThresholdName;
  readonly limit: number;
  readonly actual: number;
  readonly ok: boolean;
}

/** Compare the summary against the thresholds, in the order they were given. */
export function evaluate(summary: Summary, thresholds: readonly Threshold[]): Verdict[] {
  return thresholds.map((threshold) => {
    if (!isThresholdName(threshold.name)) {
      throw new Error(`unknown threshold ${JSON.stringify(threshold.name)}`);
    }
    const actual = measure(summary, threshold.name);
    return { name: threshold.name, limit: threshold.limit, actual, ok: actual <= threshold.limit };
  });
}
