import test from 'node:test';
import assert from 'node:assert/strict';
import { parseHeadings, slugify, assignSlugs, renderToc } from '../src/toc.js';

test('parses atx headings', () => {
  const hs = parseHeadings('# A\n## B\n');
  assert.equal(hs.length, 2);
  assert.equal(hs[0].level, 1);
  assert.equal(hs[0].text, 'A');
});

test('ignores headings in code fences', () => {
  const hs = parseHeadings('# Real\n```\n# fake\n```\n');
  assert.equal(hs.length, 1);
});

test('parses setext headings', () => {
  const hs = parseHeadings('Title\n=====\n\nSub\n---\n');
  assert.equal(hs.length, 2);
  assert.equal(hs[0].level, 1);
  assert.equal(hs[1].level, 2);
});

test('duplicate slugs get suffixes', () => {
  const slugs = assignSlugs([{level:1,text:'Foo'},{level:1,text:'Foo'},{level:1,text:'Foo'}]).map(h=>h.slug);
  assert.deepEqual(slugs, ['foo','foo-1','foo-2']);
});

test('renders toc', () => {
  const out = renderToc([{level:1,text:'A'},{level:2,text:'B'}]);
  assert.match(out, /- \[A\]\(#a\)/);
  assert.match(out, /  - \[B\]\(#b\)/);
});

test('slugify strips punctuation', () => {
  assert.equal(slugify('Hello, World!'), 'hello-world');
});
