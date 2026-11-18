/** Line diffing with a longest-common-subsequence core and unified output. */

export type Op = " " | "-" | "+";

export interface Line {
  op: Op;
  text: string;
  /** 1-based line number in the left file, or null for additions. */
  left: number | null;
  /** 1-based line number in the right file, or null for deletions. */
  right: number | null;
}

export class DiffError extends Error {}

/** Splits a document into lines, dropping the phantom line after a final newline. */
export function toLines(text: string): string[] {
  if (text === "") return [];
  const lines = text.split("\n");
  if (lines[lines.length - 1] === "") lines.pop();
  return lines;
}

/**
 * Classic LCS table over two line arrays. O(left*right) memory, which is fine
 * for the file sizes a CLI diff is expected to handle; anything larger belongs
 * in a real diff library.
 */
export function lcsLength(left: string[], right: string[]): number[][] {
  const table: number[][] = [];
  for (let i = 0; i <= left.length; i++) {
    table.push(new Array<number>(right.length + 1).fill(0));
  }
  for (let i = left.length - 1; i >= 0; i--) {
    for (let j = right.length - 1; j >= 0; j--) {
      table[i][j] = left[i] === right[j]
        ? table[i + 1][j + 1] + 1
        : Math.max(table[i + 1][j], table[i][j + 1]);
    }
  }
  return table;
}

/** Walks the LCS table to produce the edit script in file order. */
export function diffLines(left: string[], right: string[]): Line[] {
  const table = lcsLength(left, right);
  const ops: Line[] = [];
  let i = 0;
  let j = 0;
  while (i < left.length && j < right.length) {
    if (left[i] === right[j]) {
      ops.push({ op: " ", text: left[i], left: i + 1, right: j + 1 });
      i++;
      j++;
    } else if (table[i + 1][j] >= table[i][j + 1]) {
      ops.push({ op: "-", text: left[i], left: i + 1, right: null });
      i++;
    } else {
      ops.push({ op: "+", text: right[j], left: null, right: j + 1 });
      j++;
    }
  }
  while (i < left.length) {
    ops.push({ op: "-", text: left[i], left: i + 1, right: null });
    i++;
  }
  while (j < right.length) {
    ops.push({ op: "+", text: right[j], left: null, right: j + 1 });
    j++;
  }
  return ops;
}

export interface Hunk {
  leftStart: number;
  leftCount: number;
  rightStart: number;
  rightCount: number;
  lines: Line[];
}

/**
 * Groups the edit script into hunks, keeping `context` unchanged lines around
 * each change. Two change groups closer than 2*context lines merge.
 */
export function hunks(ops: Line[], context: number): Hunk[] {
  if (context < 0) throw new DiffError("context must not be negative");
  const changed = ops
    .map((line, index) => (line.op === " " ? -1 : index))
    .filter((index) => index >= 0);
  if (changed.length === 0) return [];

  const groups: Array<[number, number]> = [];
  for (const index of changed) {
    const last = groups[groups.length - 1];
    const unchanged = last ? index - last[1] - 1 : 0;
    if (last && unchanged <= 2 * context) {
      last[1] = index;
    } else {
      groups.push([index, index]);
    }
  }

  return groups.map(([first, last]) => {
    const start = Math.max(0, first - context);
    const end = Math.min(ops.length - 1, last + context);
    const lines = ops.slice(start, end + 1);
    const leftLines = lines.filter((line) => line.left !== null);
    const rightLines = lines.filter((line) => line.right !== null);
    // GNU diff reports an empty side as the line it would have followed, so a
    // deletion-only hunk still points at a real position in the right file.
    const leftBefore = ops.slice(0, start).filter((line) => line.left !== null).length;
    const rightBefore = ops.slice(0, start).filter((line) => line.right !== null).length;
    return {
      leftStart: leftLines.length ? leftLines[0].left! : leftBefore,
      leftCount: leftLines.length,
      rightStart: rightLines.length ? rightLines[0].right! : rightBefore,
      rightCount: rightLines.length,
      lines,
    };
  });
}

function range(start: number, count: number): string {
  if (count === 0) return `${start},0`;
  if (count === 1) return `${start}`;
  return `${start},${count}`;
}

/** Renders the unified diff body; the caller adds the ---/+++ header. */
export function unifiedBody(ops: Line[], context: number): string[] {
  const out: string[] = [];
  for (const hunk of hunks(ops, context)) {
    out.push(
      `@@ -${range(hunk.leftStart, hunk.leftCount)} +${range(hunk.rightStart, hunk.rightCount)} @@`,
    );
    for (const line of hunk.lines) out.push(`${line.op}${line.text}`);
  }
  return out;
}

export interface Stats {
  added: number;
  removed: number;
  changed: boolean;
}

export function stats(ops: Line[]): Stats {
  let added = 0;
  let removed = 0;
  for (const line of ops) {
    if (line.op === "+") added++;
    if (line.op === "-") removed++;
  }
  return { added, removed, changed: added > 0 || removed > 0 };
}

export function formatStats(name: string, counts: Stats): string {
  if (!counts.changed) return `${name}: no changes`;
  const total = counts.added + counts.removed;
  return `${name}: ${counts.added} insertion(s), ${counts.removed} deletion(s), ${total} change(s)`;
}

/** Word-level split used by --word mode: keeps whitespace as its own tokens. */
export function words(text: string): string[] {
  return text.match(/\S+|\s+/g) ?? [];
}
