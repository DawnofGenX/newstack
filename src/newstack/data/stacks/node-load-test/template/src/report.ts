//! The artefact: a JSON report you can archive, diff and re-gate months later.

import type { Summary } from "./stats.js";
import type { Threshold } from "./types.js";
import type { Verdict } from "./thresholds.js";
import type { Sample } from "./types.js";

export interface Report {
  readonly format: 1;
  readonly target: string;
  readonly startedAt: string;
  readonly node: string;
  readonly requests: number;
  readonly concurrency: number;
  readonly warmup: number;
  readonly wallMs: number;
  readonly requestsPerSecond: number;
  readonly summary: Summary;
  readonly thresholds: readonly Verdict[];
  readonly passed: boolean;
}

export interface ReportInput {
  readonly target: string;
  readonly startedAt: string;
  readonly requests: number;
  readonly concurrency: number;
  readonly warmup: number;
  readonly wallMs: number;
  readonly summary: Summary;
  readonly thresholds: readonly Verdict[];
}

export function build(input: ReportInput): Report {
  const seconds = input.wallMs / 1000;
  return {
    format: 1,
    target: input.target,
    startedAt: input.startedAt,
    node: process.version,
    requests: input.requests,
    concurrency: input.concurrency,
    warmup: input.warmup,
    wallMs: Math.round(input.wallMs * 1000) / 1000,
    requestsPerSecond: seconds > 0 ? Math.round((input.summary.count / seconds) * 10) / 10 : 0,
    summary: input.summary,
    thresholds: input.thresholds,
    passed: input.thresholds.every((verdict) => verdict.ok),
  };
}

/** Samples are serialised so a report can be replayed without re-running the load. */
export function samplesOf(samples: readonly Sample[]): { latencyMs: number; ok: boolean }[] {
  return samples.map((sample) => ({
    latencyMs: Math.round(sample.latencyMs * 1000) / 1000,
    ok: sample.ok,
  }));
}

function pad(text: string, width: number): string {
  return text.length >= width ? text : text + " ".repeat(width - text.length);
}

export function render(report: Report): string {
  const { summary } = report;
  const percent = (summary.errorRate * 100).toFixed(2);
  const lines = [
    `target     ${report.target}`,
    `samples    ${summary.count} measured, ${summary.warmup} warm-up, ${summary.errors} errors (${percent}%)`,
    `latency    p50 ${summary.p50}  p95 ${summary.p95}  p99 ${summary.p99}  max ${summary.max}  mean ${summary.mean} ms`,
    `percentile nearest-rank`,
    `throughput ${report.requestsPerSecond} req/s over ${(report.wallMs / 1000).toFixed(3)} s`,
  ];
  for (const verdict of report.thresholds) {
    const state = verdict.ok ? "ok" : "FAILED";
    lines.push(`threshold  ${pad(verdict.name, 9)} <= ${pad(String(verdict.limit), 6)} ${state} ${verdict.actual}`);
  }
  const failed = report.thresholds.filter((verdict) => !verdict.ok).length;
  lines.push(failed === 0 ? "result     PASS" : `result     FAIL (${failed} threshold(s))`);
  return lines.join("\n");
}

/** Samples as they appear on disk, for `replay`. */
export interface SampleFile {
  readonly samples: readonly { latencyMs: number; ok?: boolean }[];
}
