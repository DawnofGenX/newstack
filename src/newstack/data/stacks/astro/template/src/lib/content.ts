/**
 * A single selling point rendered on the landing page.
 */
export interface Feature {
  readonly title: string;
  readonly summary: string;
}

/**
 * Format a count together with the right noun, e.g. `formatCount(1, "feature")`.
 *
 * The plural is passed in explicitly so the helper also works for irregular
 * nouns (`formatCount(2, "entry", "entries")`).
 */
export function formatCount(count: number, singular: string, plural = `${singular}s`): string {
  if (!Number.isInteger(count) || count < 0) {
    throw new RangeError(`count must be a non-negative integer, got ${count}`);
  }
  return `${count} ${count === 1 ? singular : plural}`;
}
