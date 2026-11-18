import { test } from 'node:test';
import assert from 'node:assert/strict';
import { lintMarkdown } from '../src/lint.js';

test('clean markdown has no issues', () => {
  const md = '# Title\n\nSome text.\n\n```js\nconsole.log(1);\n```\n';
  assert.deepEqual(lintMarkdown(md), []);
});

test('trailing spaces flagged', () => {
  const issues = lintMarkdown('# Title\n\nLine with trailing   \n');
  assert.ok(issues.some((i) => i.rule === 'MD009'));
});

test('long line flagged', () => {
  const issues = lintMarkdown('# Title\n\n' + 'a'.repeat(200) + '\n');
  assert.ok(issues.some((i) => i.rule === 'MD013'));
});

test('unclosed fence flagged', () => {
  const issues = lintMarkdown('# Title\n\n```js\nconsole.log(1)\n');
  assert.ok(issues.some((i) => i.rule === 'MD040'));
});

test('heading skip flagged', () => {
  const issues = lintMarkdown('# Title\n\n### Deep\n');
  assert.ok(issues.some((i) => i.rule === 'MD001'));
});
