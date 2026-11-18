#!/usr/bin/env node
import { normalizeUrl } from './normalize.js';

const input = process.argv[2];
if (!input) {
  console.error('usage: node src/cli.js <url>');
  process.exit(2);
}
console.log(normalizeUrl(input));
