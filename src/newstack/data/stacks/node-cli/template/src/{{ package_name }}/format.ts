import type { Counts } from "./count.js";

export type { Counts };

export interface FileCounts extends Counts {
  path: string;
  /** Set when the file could not be read; the counts are then all zero. */
  error?: string;
}

export interface Report {
  files: FileCounts[];
  total: Counts;
}

const HEADER = ["lines", "words", "bytes"] as const;

function width(values: readonly number[]): number {
  return Math.max(...values.map((value) => String(value).length));
}

function pad(text: string, size: number): string {
  return text.padStart(size, " ");
}

/**
 * A wc-style table. Numbers are right aligned so a column of counts stays
 * scannable, and unreadable files show `?` rather than `0` — a zero that means
 * "could not read" is a lie the reader cannot detect.
 */
export function renderTable(report: Report): string {
  const rows = report.files.map((file) => [
    file.error === undefined ? String(file.lines) : "?",
    file.error === undefined ? String(file.words) : "?",
    file.error === undefined ? String(file.bytes) : "?",
    file.error === undefined ? file.path : `${file.path}: ${file.error}`,
  ]);
  if (report.files.length > 1) {
    rows.push([
      String(report.total.lines),
      String(report.total.words),
      String(report.total.bytes),
      "total",
    ]);
  }
  const sizes = HEADER.map((_, column) =>
    Math.max(...rows.map((row) => (row[column] ?? "").length), (HEADER[column] ?? "").length,),
  );
  const lines = [
    HEADER.map((name, column) => pad(name, sizes[column] ?? 0)).join(" "),
    ...rows.map((row) =>
      row.map((cell, column) => pad(cell, sizes[column] ?? 0)).join(" "),
    ),
  ];
  return `${lines.join("\n")}\n`;
}

export function renderJson(report: Report): string {
  return `${JSON.stringify(report, null, 2)}\n`;
}
