'use strict';

const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { test } = require('node:test');

const entry = path.join(__dirname, '..', 'src', 'index.js');

// Runs the entry point the way the runner does: inputs in the environment, outputs
// and the step summary in files. The temporary workspace is always removed.
function runAction(inputs, extraEnv = {}) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'action-run-'));
  const output = path.join(directory, 'output.txt');
  const summary = path.join(directory, 'summary.md');

  try {
    fs.writeFileSync(path.join(directory, 'sample.txt'), 'one two\nthree\n');
    fs.writeFileSync(output, '');
    fs.writeFileSync(summary, '');

    let stdout = '';
    let status = 0;

    try {
      stdout = execFileSync(process.execPath, [entry], {
        cwd: directory,
        encoding: 'utf8',
        env: {
          PATH: process.env.PATH,
          INPUT_PATHS: inputs,
          GITHUB_OUTPUT: output,
          GITHUB_STEP_SUMMARY: summary,
          ...extraEnv,
        },
      });
    } catch (error) {
      stdout = String(error.stdout || '');
      status = error.status;
    }

    return {
      status,
      stdout,
      output: fs.readFileSync(output, 'utf8'),
      summary: fs.readFileSync(summary, 'utf8'),
    };
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
}

test('writes totals to GITHUB_OUTPUT', () => {
  const result = runAction('sample.txt');

  assert.equal(result.status, 0);
  assert.equal(result.output, 'lines=2\nwords=3\nbytes=14\n');
});

test('writes a summary table', () => {
  const result = runAction('sample.txt');

  assert.match(result.summary, /### File sizes/);
  assert.match(result.summary, /\| `sample\.txt` \| 2 \| 3 \| 14 \|/);
});

test('honours the title input', () => {
  const result = runAction('sample.txt', { INPUT_TITLE: 'Lines per file' });

  assert.match(result.summary, /### Lines per file/);
});

test('fails the step when no path is given', () => {
  const result = runAction('');

  assert.equal(result.status, 1);
  assert.match(result.stdout, /::error::the `paths` input is empty/);
  assert.equal(result.output, '');
});
