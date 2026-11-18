// Dependency-free line diff: LCS walk plus unified hunk rendering.

function splitLines(text) {
  const lines = text.split("\n");
  if (lines.length > 0 && lines[lines.length - 1] === "") lines.pop();
  return lines;
}

function lcsTable(a, b) {
  const table = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i -= 1) {
    for (let j = b.length - 1; j >= 0; j -= 1) {
      table[i][j] = a[i] === b[j] ? table[i + 1][j + 1] + 1 : Math.max(table[i + 1][j], table[i][j + 1]);
    }
  }
  return table;
}

/** Operations {op: " " | "-" | "+", line, aLine, bLine} walking the LCS. */
export function diffLines(oldText, newText) {
  const a = splitLines(oldText);
  const b = splitLines(newText);
  const table = lcsTable(a, b);
  const ops = [];
  let i = 0;
  let j = 0;
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) {
      ops.push({ op: " ", line: a[i], aLine: i + 1, bLine: j + 1 });
      i += 1;
      j += 1;
    } else if (j < b.length && (i >= a.length || table[i][j + 1] > table[i + 1][j])) {
      ops.push({ op: "+", line: b[j], aLine: null, bLine: j + 1 });
      j += 1;
    } else {
      ops.push({ op: "-", line: a[i], aLine: i + 1, bLine: null });
      i += 1;
    }
  }
  return ops;
}

/** Groups operations into hunks with `context` unchanged lines around each change. */
export function hunks(ops, context = 3) {
  const changes = ops.map((op, index) => ({ op, index })).filter((entry) => entry.op.op !== " ");
  if (changes.length === 0) return [];
  const ranges = [];
  for (const { index } of changes) {
    const start = Math.max(0, index - context);
    const end = Math.min(ops.length - 1, index + context);
    const last = ranges[ranges.length - 1];
    if (last && start <= last.end + 1) {
      last.end = Math.max(last.end, end);
    } else {
      ranges.push({ start, end });
    }
  }
  return ranges.map(({ start, end }) => {
    const slice = ops.slice(start, end + 1);
    const oldCount = slice.filter((op) => op.op !== "+").length;
    const newCount = slice.filter((op) => op.op !== "-").length;
    const firstOld = slice.find((op) => op.op !== "+");
    const firstNew = slice.find((op) => op.op !== "-");
    return {
      oldStart: firstOld ? firstOld.aLine : 0,
      oldCount,
      newStart: firstNew ? firstNew.bLine : 0,
      newCount,
      lines: slice,
    };
  });
}

/** Unified diff text, or "" when the inputs match. */
export function unifiedDiff(oldText, newText, { oldLabel = "a", newLabel = "b", context = 3 } = {}) {
  const groups = hunks(diffLines(oldText, newText), context);
  if (groups.length === 0) return "";
  const out = [`--- ${oldLabel}`, `+++ ${newLabel}`];
  for (const group of groups) {
    out.push(`@@ -${group.oldStart},${group.oldCount} +${group.newStart},${group.newCount} @@`);
    for (const op of group.lines) out.push(op.op + op.line);
  }
  return out.join("\n") + "\n";
}
