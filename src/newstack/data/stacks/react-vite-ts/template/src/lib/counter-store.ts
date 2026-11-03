/**
 * Demo counters persist across reloads. One contract, every stack:
 * the key is "newstack:counter", a stored value is clamped to a non-negative integer,
 * and storage failures (private mode, quota, SSR) degrade to an in-memory counter.
 */

export const COUNTER_KEY = "newstack:counter";

export function clampCount(value: unknown): number {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed)) return 0;
  return Math.max(0, Math.trunc(parsed));
}

export function readCounter(): number {
  try {
    return clampCount(globalThis.localStorage?.getItem(COUNTER_KEY) ?? null);
  } catch {
    return 0;
  }
}

export function writeCounter(value: number): void {
  try {
    globalThis.localStorage?.setItem(COUNTER_KEY, String(clampCount(value)));
  } catch {
    /* storage is best effort: the counter still works in memory */
  }
}
