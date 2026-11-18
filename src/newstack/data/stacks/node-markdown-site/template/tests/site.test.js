import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { buildSite } from '../src/site.js';

function tmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'site-'));
}

test('renders a fixture page with title and body', () => {
  const input = tmp();
  const output = tmp();
  fs.writeFileSync(path.join(input, 'index.md'), '---\ntitle: Hello World\n---\n# Heading\n\nSome body text.\n');
  buildSite(input, output);
  const html = fs.readFileSync(path.join(output, 'index.html'), 'utf8');
  assert.match(html, /<title>Hello World<\/title>/);
  assert.match(html, /Some body text\./);
  assert.match(html, /<h1>Hello World<\/h1>/);
});

test('escapes title and body HTML', () => {
  const input = tmp();
  const output = tmp();
  fs.writeFileSync(path.join(input, 'x.md'), '---\ntitle: <script>alert(1)</script>\n---\nRaw <img src=x onerror=alert(2)> text.\n');
  buildSite(input, output);
  const html = fs.readFileSync(path.join(output, 'x.html'), 'utf8');
  assert.doesNotMatch(html, /<script>alert\(1\)<\/script>/);
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
  assert.match(html, /&lt;img src=x onerror=alert\(2\)&gt;/);
});