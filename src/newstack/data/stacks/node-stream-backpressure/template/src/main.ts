import { fileURLToPath } from "node:url";

import { render } from "./demo.js";
import { run as measureRun } from "./pipeline.js";
import type { Mode } from "./pipeline.js";
import { CHUNK_BYTES, chunkSeries, kib, ratio } from "./types.js";
import type { Measure } from "./types.js";

export const PROGRAM = "{{ npm_name }}";
export const VERSION = "0.1.0";

export const EXIT_OK = 0;
export const EXIT_STALLED = 1;
export const EXIT_UNUSABLE = 2;

export class UsageError extends Error {}

export const USAGE = `usage: ${PROGRAM} <command> [options]

commands:
  compare  [--chunks N] [--latency MS] [--highwater BYTES] [--max-peak-chunks N]
  demo
  --version | --help

compare streams the same chunk series three ways and checks that the mode that honours
backpressure keeps the buffer within --max-peak-chunks (default 2) of the chunk size.

exit codes: 0 ok, 1 a buffer bound was breached, 2 unusable input
`;

type Options = Record<string, string>;

function parse(argv: readonly string[]): { command: string; options: Options } {
  const [command, ...rest] = argv;
  if (command === undefined) throw new UsageError("no command given");
  const options: Options = {};
  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (token === undefined) break;
    if (!token.startsWith("--")) throw new UsageError(`unexpected argument ${token}`);
    const name = token.slice(2);
    const value = rest[index + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new UsageError(`--${name} needs a value`);
    }
    options[name] = value;
    index += 1;
  }
  return { command, options };
}

function integer(options: Options, name: string, fallback: number): number {
  const raw = options[name];
  if (raw === undefined) return fallback;
  const value = Number(raw);
  if (!Number.isInteger(value) || value < 0) {
    throw new UsageError(`--${name} must be an integer >= 0, got ${raw}`);
  }
  return value;
}

function tableLine(measure: Measure, chunk: number): string {
  return [
    `  ${measure.mode.padEnd(10)}`,
    `peak ${kib(measure.peakBuffered).padStart(10)}`,
    `(${ratio(measure.peakBuffered, chunk).padStart(14)})`,
    `waits ${String(measure.waits).padStart(4)}`,
    `${String(measure.ms).padStart(6)} ms`,
    `delivered ${kib(measure.bytes)}`,
  ].join("  ");
}

export async function run(argv: readonly string[]): Promise<number> {
  const head = argv[0];
  if (head === "--version" || head === "version") {
    console.log(`${PROGRAM} ${VERSION}`);
    return EXIT_OK;
  }
  if (head === undefined || head === "--help" || head === "help") {
    console.log(USAGE.replace(/\n$/, ""));
    return EXIT_OK;
  }
  try {
    const { command, options } = parse(argv);

    if (command === "demo") {
      console.log(await render());
      return EXIT_OK;
    }

    if (command === "compare") {
      const chunks = integer(options, "chunks", 256);
      const latency = integer(options, "latency", 1);
      const highWaterMark = integer(options, "highwater", CHUNK_BYTES);
      const bound = integer(options, "max-peak-chunks", 2);
      if (chunks < 1) throw new UsageError("--chunks must be at least 1");
      if (highWaterMark < 1) throw new UsageError("--highwater must be at least 1");
      const series = chunkSeries(chunks);
      const modes: Mode[] = ["ignoring", "awaiting", "honoring"];
      const measures: Measure[] = [];
      for (const mode of modes) {
        measures.push(await measureRun(mode, series, { highWaterMark, latencyMs: latency }));
      }
      console.log(
        `${chunks} chunks of ${kib(CHUNK_BYTES)} through a sink taking one per ${latency} ms`,
      );
      for (const measure of measures) console.log(tableLine(measure, CHUNK_BYTES));
      const honoring = measures.find((measure) => measure.mode === "honoring");
      if (honoring === undefined) throw new Error("honoring mode did not run");
      const limit = bound * CHUNK_BYTES;
      const bounded = honoring.peakBuffered <= limit;
      console.log(
        `bounded    ${bounded ? "yes" : "NO"}: peak ${kib(honoring.peakBuffered)} ` +
          `against a limit of ${kib(limit)}`,
      );
      return bounded ? EXIT_OK : EXIT_STALLED;
    }

    throw new UsageError(`unknown command ${command}`);
  } catch (error) {
    if (error instanceof UsageError) {
      console.error(`${PROGRAM}: ${error.message}`);
      console.error(`try: ${PROGRAM} --help`);
      return EXIT_UNUSABLE;
    }
    throw error;
  }
}

if (process.argv[1] !== undefined && fileURLToPath(import.meta.url) === process.argv[1]) {
  process.exitCode = await run(process.argv.slice(2));
}
