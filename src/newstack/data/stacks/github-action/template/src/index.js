'use strict';

const fs = require('node:fs');

const { countFiles, parsePaths, renderMarkdown, totals } = require('./report');

/**
 * Reads an action input the way GitHub passes it: `INPUT_<NAME>`, uppercased.
 *
 * @param {string} name
 * @param {string} [fallback]
 * @returns {string}
 */
function input(name, fallback = '') {
  const value = process.env[`INPUT_${name.toUpperCase()}`];
  return value === undefined || value === '' ? fallback : value;
}

function fail(message) {
  console.log(`::error::${message}`);
  process.exitCode = 1;
}

function main() {
  const paths = parsePaths(input('paths'));

  if (paths.length === 0) {
    fail('the `paths` input is empty: pass at least one file');
    return;
  }

  let rows;
  try {
    rows = countFiles(paths);
  } catch (error) {
    fail(`could not count the given paths: ${error.message}`);
    return;
  }

  const sum = totals(rows);
  const table = renderMarkdown(rows, { title: input('title', 'File sizes') });

  console.log(table);

  // Step summary and outputs are files filled in by the runner; when the action
  // runs outside Actions they are unset, so the same binary stays testable.
  if (process.env.GITHUB_STEP_SUMMARY) {
    fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, table);
  }

  if (process.env.GITHUB_OUTPUT) {
    fs.appendFileSync(
      process.env.GITHUB_OUTPUT,
      [`lines=${sum.lines}`, `words=${sum.words}`, `bytes=${sum.bytes}`].join('\n') + '\n',
    );
  }
}

main();
