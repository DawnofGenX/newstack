//! Command line entry point: `run`, `replay`, `--selftest`.

import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { load } from "./client.js";
import { build, render, samplesOf, type SampleFile } from "./report.js";
import { run as selftest } from "./selftest.js";
import { summarize } from "./stats.js";
import { evaluate, parseThresholds } from "./thresholds.js";
import type { Sample, Threshold } from "./types.js";

const VERSION = "0.1.0";

export const EXIT_OK = 0;
export const EXIT_BREACH = 1;
export const EXIT_UNUSABLE = 2;

const USAGE = `usage: {{ npm_name }} run --target URL [options]
       {{ npm_name }} replay --samples FILE [options]
       {{ npm_name }} --selftest
       {{ npm_name }} --version

run options
  --target URL          where to send GET requests (required)
  --requests N          requests to send, wall clock is whatever they take (100)
  --concurrency N       workers sharing one keep-alive agent (4)
  --warmup N            leading samples excluded from the summary (5)
  --timeout MS          per request budget (5000)
  --threshold n=v       repeatable: p50, p90, p95, p99, max, mean, errorRate
  --json PATH           also write the report, samples included

replay options
  --samples FILE        JSON {\"samples\": [{\"latencyMs\": 1.2, \"ok\": true}]}
  --warmup N  --threshold n=v  --json PATH

exit codes: 0 thresholds passed, 1 a threshold failed, 2 the run was unusable
`;

class UsageError extends Error {}

interface Parsed {
  readonly command: string;
  readonly single: Map<string, string>;
  readonly repeated: Map<string, string[]>;
  readonly switches: Set<string>;
}

function parseArguments(argv: readonly string[]): Parsed {
  const command = argv[0] ?? "";
  if (!["run", "replay", "help"].includes(command)) {
    throw new UsageError(`unknown command ${JSON.stringify(command)}`);
  }
  const single = new Map<string, string>();
  const repeated = new Map<string, string[]>();
  const switches = new Set<string>();
  let index = 1;
  while (index < argv.length) {
    const raw = argv[index] as string;
    if (!raw.startsWith("--")) throw new UsageError(`unexpected argument ${JSON.stringify(raw)}`);
    const at = raw.indexOf("=");
    const name = at > 0 ? raw.slice(2, at) : raw.slice(2);
    if (name === "threshold") {
      const value = at > 0 ? raw.slice(at + 1) : (argv[index + 1] ?? "");
      if (at < 0) index += 1;
      const list = repeated.get(name) ?? [];
      list.push(value);
      repeated.set(name, list);
      index += 1;
      continue;
    }
    if (["target", "requests", "concurrency", "warmup", "timeout", "json", "samples"].includes(name)) {
      const value = at > 0 ? raw.slice(at + 1) : (argv[index + 1] ?? "");
      if (value === "") throw new UsageError(`--${name} needs a value`);
      if (at < 0) index += 1;
      single.set(name, value);
      index += 1;
      continue;
    }
    throw new UsageError(`unknown option ${JSON.stringify(raw)}`);
  }
  return { command, single, repeated, switches };
}

function integer(parsed: Parsed, name: string, fallback: number): number {
  const raw = parsed.single.get(name);
  if (raw === undefined) return fallback;
  const value = Number(raw);
  if (!Number.isInteger(value) || value < 0) {
    throw new UsageError(`--${name} needs a whole number, got ${JSON.stringify(raw)}`);
  }
  return value;
}

function thresholdsOf(parsed: Parsed): { thresholds: Threshold[]; note: string } {
  const raw = parsed.repeated.get("threshold") ?? [];
  if (raw.length === 0) {
    return {
      thresholds: [{ name: "errorRate", limit: 0 }],
      note: "no --threshold given, defaulting to errorRate <= 0",
    };
  }
  return { thresholds: parseThresholds(raw), note: "" };
}

function reportTo(path: string, payload: unknown): void {
  writeFileSync(path, `${JSON.stringify(payload, null, 2)}\n`);
}

async function commandRun(parsed: Parsed): Promise<number> {
  const target = parsed.single.get("target");
  if (target === undefined) throw new UsageError("run needs --target");
  const requests = integer(parsed, "requests", 100);
  const concurrency = integer(parsed, "concurrency", 4);
  const warmup = integer(parsed, "warmup", 5);
  const timeout = integer(parsed, "timeout", 5000);
  if (requests < 1) throw new UsageError("--requests must be at least 1");
  if (concurrency < 1) throw new UsageError("--concurrency must be at least 1");
  if (warmup >= requests) {
    throw new UsageError(`--warmup ${warmup} of ${requests} would leave nothing measured`);
  }
  try {
    new URL(target);
  } catch {
    throw new UsageError(`--target is not a URL: ${JSON.stringify(target)}`);
  }

  const { thresholds, note } = thresholdsOf(parsed);
  if (note !== "") process.stdout.write(`note       ${note}\n`);
  const { samples, wallMs } = await load({ url: target, requests, concurrency, timeoutMs: timeout });
  const summary = summarize(samples, warmup);
  const verdicts = evaluate(summary, thresholds);
  const report = build({
    target,
    startedAt: new Date().toISOString(),
    requests,
    concurrency,
    warmup,
    wallMs,
    summary,
    thresholds: verdicts,
  });
  process.stdout.write(`${render(report)}\n`);
  const json = parsed.single.get("json");
  if (json !== undefined) {
    reportTo(json, { ...report, samples: samplesOf(samples) });
    process.stdout.write(`wrote      ${json}\n`);
  }
  return report.passed ? EXIT_OK : EXIT_BREACH;
}

function sampleFile(path: string): Sample[] {
  let parsed: unknown;
  try {
    parsed = JSON.parse(readFileSync(path, "utf8")) as unknown;
  } catch (error) {
    throw new UsageError(`cannot read ${path}: ${(error as Error).message}`);
  }
  const file = parsed as SampleFile;
  if (!Array.isArray(file.samples)) {
    throw new UsageError(`${path} needs a \"samples\" array`);
  }
  return file.samples.map((entry, index) => {
    if (typeof entry.latencyMs !== "number" || !Number.isFinite(entry.latencyMs)) {
      throw new UsageError(`${path}: sample ${index} needs a numeric latencyMs`);
    }
    const ok = entry.ok ?? true;
    const sample: Sample = {
      index,
      dueAt: 0n,
      latencyMs: entry.latencyMs,
      status: ok ? 200 : 0,
      ok,
    };
    return sample;
  });
}

function commandReplay(parsed: Parsed): number {
  const path = parsed.single.get("samples");
  if (path === undefined) throw new UsageError("replay needs --samples");
  const samples = sampleFile(path);
  const warmup = integer(parsed, "warmup", 0);
  if (warmup >= samples.length) {
    throw new UsageError(`--warmup ${warmup} of ${samples.length} would leave nothing measured`);
  }
  const { thresholds, note } = thresholdsOf(parsed);
  if (note !== "") process.stdout.write(`note       ${note}\n`);
  const summary = summarize(samples, warmup);
  const verdicts = evaluate(summary, thresholds);
  const report = build({
    target: `replay:${path}`,
    startedAt: new Date().toISOString(),
    requests: samples.length,
    concurrency: 0,
    warmup,
    wallMs: 0,
    summary,
    thresholds: verdicts,
  });
  process.stdout.write(`${render(report)}\n`);
  const json = parsed.single.get("json");
  if (json !== undefined) {
    reportTo(json, report);
    process.stdout.write(`wrote      ${json}\n`);
  }
  return report.passed ? EXIT_OK : EXIT_BREACH;
}

export async function main(argv: readonly string[] = process.argv.slice(2)): Promise<number> {
  if (argv.length === 0 || argv[0] === "help" || argv[0] === "--help") {
    process.stdout.write(USAGE);
    return EXIT_OK;
  }
  if (argv[0] === "--version") {
    process.stdout.write(`{{ npm_name }} ${VERSION}\n`);
    return EXIT_OK;
  }
  if (argv[0] === "--selftest") return selftest();
  try {
    const parsed = parseArguments(argv);
    if (parsed.command === "run") return await commandRun(parsed);
    return commandReplay(parsed);
  } catch (error) {
    process.stderr.write(`{{ npm_name }}: ${(error as Error).message}\n`);
    process.stderr.write("try --help\n");
    return EXIT_UNUSABLE;
  }
}

const invoked = process.argv[1];
if (invoked !== undefined && fileURLToPath(import.meta.url) === invoked) {
  void main().then((code) => process.exit(code));
}
