import { fileURLToPath } from 'node:url';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type { Account } from './demo.js';
import { accounts, scenarios } from './demo.js';
import { catchUp, readCheckpoint, rebuild, writeCheckpoint } from './projection.js';
import { EventStore } from './store.js';
import { ConcurrencyError, StoreError } from './types.js';

export const PROGRAM = '{{ npm_name }}';
export const VERSION = '0.1.0';

export const EXIT_OK = 0;
export const EXIT_REFUSED = 1;
export const EXIT_UNUSABLE = 2;

class UsageError extends Error {}

interface Options {
  [key: string]: string[];
}

function parse(argv: readonly string[]): { command: string; options: Options; rest: string[] } {
  const rest: string[] = [];
  const options: Options = {};
  let command = '';
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index] as string;
    if (arg.startsWith('--')) {
      const [name, inline] = arg.slice(2).split('=', 2);
      if (name === undefined || name === '') throw new UsageError('empty option name');
      let value: string | undefined = inline;
      if (value === undefined) {
        const next = argv[index + 1];
        if (next === undefined || next.startsWith('--')) {
          throw new UsageError(`--${name} needs a value`);
        }
        value = next;
        index += 1;
      }
      options[name] = [...(options[name] ?? []), value];
      continue;
    }
    if (command === '') command = arg;
    else rest.push(arg);
  }
  return { command, options, rest };
}

function one(options: Options, name: string, fallback?: string): string {
  const values = options[name];
  if (values === undefined || values.length === 0) {
    if (fallback !== undefined) return fallback;
    throw new UsageError(`--${name} is required`);
  }
  return values[values.length - 1] as string;
}

function many(options: Options, name: string): string[] {
  return options[name] ?? [];
}

export const USAGE = `usage: ${PROGRAM} <command> [options]

commands:
  append   --log PATH --stream NAME --expected-version N --type TYPE [--data JSON]...
  read     --log PATH [--stream NAME] [--from N]
  project  --log PATH --checkpoint PATH
  demo
  --selftest | --version | --help

exit codes: 0 ok, 1 refused (a version conflict), 2 unusable input
`;

function format(event: { stream: string; version: number; position: number; type: string; data: unknown }): string {
  return `#${event.position}  ${event.stream} v${event.version}  ${event.type}  ${JSON.stringify(event.data)}`;
}

export function run(argv: readonly string[]): number {
  // Bare flags carry no value, so they are recognised before the option parser,
  // which would otherwise report "--version needs a value".
  const head = argv[0];
  if (head === '--version' || head === 'version') {
    console.log(`${PROGRAM} ${VERSION}`);
    return EXIT_OK;
  }
  if (head === undefined || head === '--help' || head === 'help') {
    console.log(USAGE.replace(/\n$/, ''));
    return EXIT_OK;
  }
  const { command, options } = parse(argv);

  if (command === 'append') {
    const log = one(options, 'log');
    const stream = one(options, 'stream');
    const expected = Number(one(options, 'expected-version'));
    if (!Number.isInteger(expected) || expected < 0) {
      throw new UsageError(`--expected-version must be an integer >= 0, got ${expected}`);
    }
    const events = many(options, 'data').map((raw, index) => {
      const data = raw === 'null' ? {} : (JSON.parse(raw) as unknown);
      const type = many(options, 'type')[index] ?? many(options, 'type')[0];
      if (type === undefined) throw new UsageError('--type is required');
      return { type, data };
    });
    if (events.length === 0) {
      throw new UsageError('append needs at least one --data');
    }
    const store = EventStore.open(log);
    try {
      const result = store.append(stream, expected, events);
      for (const event of result.events) console.log(format(event));
      return EXIT_OK;
    } catch (error) {
      if (error instanceof ConcurrencyError) {
        console.error(`${PROGRAM}: ${error.message}`);
        return EXIT_REFUSED;
      }
      throw error;
    }
  }

  if (command === 'read') {
    const log = one(options, 'log');
    const from = Number(one(options, 'from', '0'));
    const store = EventStore.open(log);
    const events = options['stream']
      ? store.readStream(one(options, 'stream'), from)
      : store.readAll(from);
    if (events.length === 0) {
      console.log(`${PROGRAM}: the log holds no events at or after ${from}`);
      return EXIT_OK;
    }
    for (const event of events) console.log(format(event));
    console.log(`${events.length} event(s), position ${store.position}`);
    return EXIT_OK;
  }

  if (command === 'project') {
    const log = one(options, 'log');
    const checkpoint = one(options, 'checkpoint');
    const store = EventStore.open(log);
    const saved = readCheckpoint<Account>(checkpoint);
    // Resume from the saved state, not from an assumption about it: catching up
    // from `accounts.initial` whenever the checkpoint says "position 7" would
    // fold the first seven events into a state that already contains them.
    const start = saved.state ?? accounts.initial;
    const caught = catchUp(store, accounts, start, saved.position);
    writeCheckpoint(checkpoint, caught.position, caught.state);
    const full = rebuild(store, accounts);
    const same = JSON.stringify(full.state) === JSON.stringify(caught.state);
    console.log(`projection  ${accounts.name}`);
    console.log(`resumed at  ${saved.position} (${saved.state === null ? 'no saved state' : 'saved state'})`);
    console.log(`checkpoint  ${saved.position} -> ${caught.position}`);
    console.log(`applied     ${caught.applied} event(s), ${caught.skipped} already folded in`);
    console.log(`balance     ${caught.state.balance}`);
    console.log(`replay      ${same ? 'matches a full rebuild' : 'DIVERGED from a full rebuild'}`);
    return same ? EXIT_OK : EXIT_REFUSED;
  }

  if (command === 'demo') {
    const directory = mkdtempSync(join(tmpdir(), 'eso-demo-'));
    try {
      for (const story of scenarios(directory)) {
        console.log(story.title);
        for (const line of story.lines) console.log(`  ${line}`);
        console.log('');
      }
      return EXIT_OK;
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  }

  throw new UsageError(`unknown command ${command}`);
}

export function main(argv: readonly string[]): number {
  try {
    return run(argv);
  } catch (error) {
    if (error instanceof UsageError) {
      console.error(`${PROGRAM}: ${error.message}`);
      console.error(`try: ${PROGRAM} --help`);
      return EXIT_UNUSABLE;
    }
    if (error instanceof StoreError) {
      console.error(`${PROGRAM}: ${error.message}`);
      return EXIT_UNUSABLE;
    }
    if (error instanceof SyntaxError) {
      console.error(`${PROGRAM}: --data is not valid JSON: ${error.message}`);
      return EXIT_UNUSABLE;
    }
    throw error;
  }
}

if (process.argv[1] !== undefined && fileURLToPath(import.meta.url) === process.argv[1]) {
  process.exitCode = main(process.argv.slice(2));
}
