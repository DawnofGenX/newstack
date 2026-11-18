import { readFileSync, writeFileSync } from 'node:fs';
import { createTwoFilesPatch, applyPatch, diffLines } from 'diff';

export function makePatch(oldFile, newFile, oldText, newText) {
  return createTwoFilesPatch(oldFile, newFile, oldText, newText, '', '', { context: 3 });
}

export function computeStat(oldText, newText) {
  const changes = diffLines(oldText, newText);
  let added = 0, removed = 0;
  for (const c of changes) {
    if (c.value === '') continue;
    const lines = c.value.split(/\n/).length - (c.value.endsWith('\n') ? 1 : 0);
    if (c.added) added += lines;
    if (c.removed) removed += lines;
  }
  return { added, removed };
}

export function applyPatchText(patchText, targetText) {
  return applyPatch(targetText, patchText);
}
