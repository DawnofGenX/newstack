import { readFileSync, writeFileSync } from 'node:fs';
import { makePatch, computeStat, applyPatchText } from './diff.js';

function usage() {
  console.log('Usage: diff <old> <new> [--stat] | diff --apply <patch> <file>');
  process.exit(0);
}

const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) usage();

if (args[0] === '--apply') {
  const patchFile = args[1];
  const targetFile = args[2];
  if (!patchFile || !targetFile) { console.error('missing args'); process.exit(2); }
  const patchText = readFileSync(patchFile, 'utf8');
  const targetText = readFileSync(targetFile, 'utf8');
  const result = applyPatchText(patchText, targetText);
  if (result === false) { console.error('apply failed'); process.exit(1); }
  writeFileSync(targetFile, result);
  console.log('applied');
  process.exit(0);
}

const oldFile = args[0];
const newFile = args[1];
if (!oldFile || !newFile) { console.error('missing files'); process.exit(2); }
const oldText = readFileSync(oldFile, 'utf8');
const newText = readFileSync(newFile, 'utf8');

if (args.includes('--stat')) {
  const s = computeStat(oldText, newText);
  console.log(`${oldFile} -> ${newFile}: ${s.added} insertions(+), ${s.removed} deletions(-)`);
  process.exit(0);
}

const patch = makePatch(oldFile, newFile, oldText, newText);
process.stdout.write(patch);
if (!patch.endsWith('\n')) process.stdout.write('\n');
