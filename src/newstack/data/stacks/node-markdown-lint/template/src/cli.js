#!/usr/bin/env node
import { lintFile } from './lint.js';

const file = process.argv[2];
if (!file) {
  console.error('usage: node src/cli.js <markdown-file>');
  process.exit(2);
}
const issues = lintFile(file);
if (issues.length === 0) {
  console.log(`OK: ${file}`);
  process.exit(0);
}
for (const issue of issues) {
  console.log(`${file}:${issue.line}: ${issue.rule} ${issue.message}`);
}
process.exit(1);
