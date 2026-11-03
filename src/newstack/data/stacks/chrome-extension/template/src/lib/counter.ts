export const COUNT_STORAGE_KEY = "newstack:counter";

/**
 * Pure counter logic. No chrome.* access here so it can be unit tested in
 * plain jsdom without a browser extension host.
 */

/** Increment the counter, clamping garbage input to a sane integer. */
export function nextCount(current: number): number {
  if (!Number.isFinite(current)) return 1;
  return Math.max(0, Math.trunc(current)) + 1;
}

/** Reset helper used by the popup's "Reset" affordance. */
export function resetCount(): number {
  return 0;
}

/** Human readable label, e.g. 1 -> "Popup clicks: 1". */
export function formatCount(count: number): string {
  const safe = Number.isFinite(count) ? Math.max(0, Math.trunc(count)) : 0;
  return `Popup clicks: ${safe}`;
}
