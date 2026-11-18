import { readFileSync } from 'node:fs';

// A small, dependency-free Markdown linter.
// Rules implemented (each returns { rule, line, message }):
//   MD009 trailing spaces
//   MD013 line length (> 120 chars)
//   MD040 fenced code blocks must be closed
//   MD001 heading levels must not skip

const MAX_LINE = 120;

export function lintMarkdown(text) {
  const issues = [];
  const lines = String(text).split(/\n/);
  let fenceOpen = null;
  let lastHeading = 0;
  lines.forEach((raw, i) => {
    const line = raw.replace(/\r$/, '');
    const n = i + 1;
    if (fenceOpen) {
      if (/^```/.test(line.trim())) fenceOpen = null;
      return;
    }
    if (/^```/.test(line.trim())) {
      fenceOpen = n;
      return;
    }
    if (/[ \t]+$/.test(line)) {
      issues.push({ rule: 'MD009', line: n, message: 'Trailing spaces' });
    }
    if (line.length > MAX_LINE) {
      issues.push({ rule: 'MD013', line: n, message: `Line length ${line.length} > ${MAX_LINE}` });
    }
    const m = /^(#{1,6})\s/.exec(line);
    if (m) {
      const level = m[1].length;
      if (lastHeading && level > lastHeading + 1) {
        issues.push({ rule: 'MD001', line: n, message: `Heading level skipped from ${lastHeading} to ${level}` });
      }
      lastHeading = level;
    }
  });
  if (fenceOpen) {
    issues.push({ rule: 'MD040', line: fenceOpen, message: 'Unclosed fenced code block' });
  }
  return issues;
}

export function lintFile(filePath) {
  return lintMarkdown(readFileSync(filePath, 'utf8'));
}

export default { lintMarkdown, lintFile };
