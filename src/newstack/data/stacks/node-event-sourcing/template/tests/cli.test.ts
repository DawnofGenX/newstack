import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, before, test } from 'node:test';
import { EXIT_OK, EXIT_REFUSED, EXIT_UNUSABLE, main } from '../src/main.js';

let directory = '';

before(() => {
  directory = mkdtempSync(join(tmpdir(), 'eso-cli-'));
});

after(() => {
  rmSync(directory, { recursive: true, force: true });
});

/** Run the CLI with stdout/stderr captured, returning the exit code and both streams. */
function cli(...argv: string[]): { code: number; out: string; err: string } {
  const out: string[] = [];
  const err: string[] = [];
  const write = process.stdout.write.bind(process.stdout);
  const error = console.error;
  const log = console.log;
  process.stdout.write = ((chunk: string) => {
    out.push(String(chunk));
    return true;
  }) as typeof process.stdout.write;
  console.log = (...parts: unknown[]) => out.push(parts.join(' ') + '\n');
  console.error = (...parts: unknown[]) => err.push(parts.join(' ') + '\n');
  try {
    const code = main(argv);
    return { code, out: out.join(''), err: err.join('') };
  } finally {
    process.stdout.write = write;
    console.log = log;
    console.error = error;
  }
}

/** Run main() without capturing, for commands whose output is not under test. */
function silent(...argv: string[]): number {
  const write = process.stdout.write.bind(process.stdout);
  const error = console.error;
  const log = console.log;
  const saved = { err: [] as string[], out: [] as string[] };
  process.stdout.write = (() => true) as typeof process.stdout.write;
  console.log = () => undefined;
  console.error = () => undefined;
  try {
    const code = main(argv);
    saved.err = [];
    return code;
  } finally {
    process.stdout.write = write;
    console.log = log;
    console.error = error;
  }
}

test('append prints one line per event', () => {
  const log = join(directory, 'append.jsonl');
  const result = cli('append', '--log', log, '--stream', 'acct', '--expected-version', '0',
    '--type', 'deposited', '--data', '{"amount":10}');
  assert.equal(result.code, EXIT_OK);
  assert.match(result.out, /#0 {2}acct v1 {2}deposited {2}\{"amount":10\}/);
});

test('a second append continues the stream', () => {
  const log = join(directory, 'append.jsonl');
  const result = cli('append', '--log', log, '--stream', 'acct', '--expected-version', '1',
    '--type', 'withdrawn', '--data', '{"amount":4}');
  assert.equal(result.code, EXIT_OK);
  assert.match(result.out, /v2/);
});

test('a stale expected version exits 1 and says why', () => {
  const log = join(directory, 'append.jsonl');
  const result = cli('append', '--log', log, '--stream', 'acct', '--expected-version', '1',
    '--type', 'deposited', '--data', '{"amount":1}');
  assert.equal(result.code, EXIT_REFUSED);
  assert.match(result.err, /version 2, not 1/);
  assert.match(result.err, /re-reading before retrying/);
});

test('malformed json exits 2', () => {
  const result = cli('append', '--log', join(directory, 'bad.jsonl'), '--stream', 'acct',
    '--expected-version', '0', '--type', 'deposited', '--data', '{oops');
  assert.equal(result.code, EXIT_UNUSABLE);
  assert.match(result.err, /not valid JSON/);
});

test('an unknown command exits 2', () => {
  const result = cli('nope');
  assert.equal(result.code, EXIT_UNUSABLE);
  assert.match(result.err, /unknown command nope/);
});

test('an append without data exits 2', () => {
  const result = cli('append', '--log', join(directory, 'empty.jsonl'), '--stream', 'a',
    '--expected-version', '0', '--type', 'x');
  assert.equal(result.code, EXIT_UNUSABLE);
  assert.match(result.err, /at least one --data/);
});

test('read prints the events and a count', () => {
  const result = cli('read', '--log', join(directory, 'append.jsonl'));
  assert.equal(result.code, EXIT_OK);
  assert.match(result.out, /2 event\(s\), position 2/);
});

test('read can start at a position', () => {
  const result = cli('read', '--log', join(directory, 'append.jsonl'), '--from', '1');
  assert.match(result.out, /1 event\(s\)/);
});

test('read of an empty log says so without failing', () => {
  const result = cli('read', '--log', join(directory, 'absent.jsonl'));
  assert.equal(result.code, EXIT_OK);
  assert.match(result.out, /holds no events/);
});

test('project reports the checkpoint it moved from and to', () => {
  const log = join(directory, 'append.jsonl');
  const checkpoint = join(directory, 'acct.checkpoint');
  const result = cli('project', '--log', log, '--checkpoint', checkpoint);
  assert.equal(result.code, EXIT_OK);
  assert.match(result.out, /checkpoint {2}0 -> 2/);
  assert.match(result.out, /balance {5}6/);
  assert.match(result.out, /replay {6}matches a full rebuild/);
});

test('projecting again resumes at the head', () => {
  const log = join(directory, 'append.jsonl');
  const checkpoint = join(directory, 'acct.checkpoint');
  const result = cli('project', '--log', log, '--checkpoint', checkpoint);
  assert.equal(result.code, EXIT_OK);
  assert.match(result.out, /resumed at {2}2 \(saved state\)/);
  assert.match(result.out, /applied {5}0 event\(s\)/);
});

test('the checkpoint file keeps the position it reports', () => {
  const checkpoint = join(directory, 'acct.checkpoint');
  const payload = JSON.parse(readFileSync(checkpoint, 'utf8')) as { position: number };
  assert.equal(payload.position, 2);
});

test('version and help exit 0', () => {
  assert.equal(silent('--version'), EXIT_OK);
  assert.equal(silent('--help'), EXIT_OK);
  assert.equal(silent(), EXIT_OK);
});

test('demo runs offline and exits 0', () => {
  assert.equal(silent('demo'), EXIT_OK);
});

test('a missing option value exits 2', () => {
  const result = cli('read', '--log');
  assert.equal(result.code, EXIT_UNUSABLE);
  assert.match(result.err, /--log needs a value/);
});

test('an option with an inline value works', () => {
  const result = cli('read', `--log=${join(directory, 'append.jsonl')}`);
  assert.equal(result.code, EXIT_OK);
});

test('a non-integer expected version exits 2', () => {
  const result = cli('append', '--log', join(directory, 'x.jsonl'), '--stream', 'a',
    '--expected-version', 'one', '--type', 'x', '--data', '{}');
  assert.equal(result.code, EXIT_UNUSABLE);
  assert.match(result.err, /integer >= 0/);
});
