import type { Counts } from "./count.js";

/** Which columns to print. `all` is the default and prints all three. */
export type Column = "lines" | "words" | "bytes";

export interface FormatOptions {
  /** Columns to include, in this order. Defaults to every column. */
  readonly columns?: readonly Column[];
  /** Right-align each number to this width. Defaults to 8, like `wc`. */
  readonly width?: number;
  /** Printed after the numbers, e.g. a file name. */
  readonly label?: string;
}

const DEFAULT_COLUMNS: readonly Column[] = ["lines", "words", "bytes"];

/**
 * Renders counts as fixed-width columns, the way `wc` prints them. Kept free of
 * console access so it is testable and usable in a browser bundle.
 */
export function formatCounts(counts: Counts, options: FormatOptions = {}): string {
  const columns = options.columns ?? DEFAULT_COLUMNS;
  const width = options.width ?? 8;

  const cells = columns.map((column) => String(counts[column]).padStart(width));

  return options.label === undefined ? cells.join("") : `${cells.join("")} ${options.label}`;
}
