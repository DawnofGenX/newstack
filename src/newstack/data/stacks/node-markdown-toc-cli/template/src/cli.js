import { readFileSync, writeFileSync } from 'node:fs';
import { parseHeadings, renderToc } from './toc.js';

function usage() {
  console.log('Usage: toc <file.md> [--write]');
  process.exit(0);
}

const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) usage();
const write = args.includes('--write');
const file = args.find((a) => !a.startsWith('--'));
if (!file) { console.error('missing file'); process.exit(2); }

const text = readFileSync(file, 'utf8');
const toc = renderToc(parseHeadings(text));
const block = `<!-- toc -->\n${toc}\n<!-- tocstop -->`;

if (!write) {
  console.log(toc);
  process.exit(0);
}

const tocRegex = /<!-- toc -->[\s\S]*?<!-- tocstop -->/;
let next;
if (tocRegex.test(text)) {
  next = text.replace(tocRegex, block);
} else {
  next = block + '\n\n' + text;
}
writeFileSync(file, next);
console.log('updated ' + file);
