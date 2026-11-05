import { fileURLToPath } from "node:url";

import { render } from "./demo.js";
import { Pool } from "./pool.js";

export const PROGRAM = "{{ npm_name }}";
export const VERSION = "0.1.0";

export const EXIT_OK = 0;
export const EXIT_BROKEN = 1;
export const EXIT_UNUSABLE = 2;

export class UsageError extends Error {}

export const USAGE = `usage: ${PROGRAM} <command> [options]

commands:
  bench  [--size N] [--tasks N] [--max-queue N]
  demo
  --version | --help

bench runs N sum tasks through a pool of N workers and fails if the pool spawned more
workers than its size, or if any task failed.

exit codes: 0 ok, 1 the pool broke its own contract, 2 unusable input
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

function integer(options: Options, name: string, fallback: number, minimum: number): number {
  const raw = options[name];
  if (raw === undefined) return fallback;
  const value = Number(raw);
  if (!Number.isInteger(value) || value < minimum) {
    throw new UsageError(`--${name} must be an integer >= ${minimum}, got ${raw}`);
  }
  return value;
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

    if (command === "bench") {
      const size = integer(options, "size", 4, 1);
      const tasks = integer(options, "tasks", 64, 1);
      const maxQueue = integer(options, "max-queue", 4_096, 0);
      const pool = new Pool({ size, maxQueue });
      const started = performance.now();
      let failures = 0;
      const results = await Promise.all(
        Array.from({ length: tasks }, (_, index) =>
          pool.run<number>("sum", { values: [index, 1] }).then(
            (value) => value,
            () => {
              failures += 1;
              return Number.NaN;
            },
          ),
        ),
      );
      const elapsed = Math.round(performance.now() - started);
      const stats = pool.stats();
      const report = await pool.close();
      console.log(`workers    ${size}`);
      console.log(`tasks      ${tasks}`);
      console.log(`elapsed    ${elapsed} ms`);
      console.log(`spawns     ${stats.spawns}`);
      console.log(`completed  ${report.completed}`);
      console.log(`failed     ${report.failed}`);
      console.log(`refused    ${report.refused}`);
      console.log(`peak queue ${stats.peakQueue}`);
      const summed = results.reduce((total, value) => total + (Number.isNaN(value) ? 0 : value), 0);
      console.log(`sum        ${summed}`);
      const held = stats.spawns <= size && failures === 0 && report.refused === 0;
      console.log(
        `contract   ${held ? "kept" : "BROKEN"}: a pool of ${size} spawned ${stats.spawns}, ` +
          `refused ${report.refused}, failed ${report.failed}`,
      );
      return held ? EXIT_OK : EXIT_BROKEN;
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
