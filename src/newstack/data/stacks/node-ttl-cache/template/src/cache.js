/**
 * A small TTL + LRU cache with counters.
 *
 * Recency comes from Map insertion order: reading an entry deletes and re-adds
 * it, so the first key in the map is always the least recently used one and
 * eviction is a one-liner. Expiry is checked on read rather than on a timer, so
 * the cache never holds a handle that keeps a process alive.
 */

export const DEFAULT_CAPACITY = 128;

export function createCache({ capacity = DEFAULT_CAPACITY, ttlMs = 0, now = Date.now } = {}) {
  if (!Number.isInteger(capacity) || capacity < 1) {
    throw new RangeError(`capacity must be a positive integer, got ${capacity}`);
  }
  if (!Number.isFinite(ttlMs) || ttlMs < 0) {
    throw new RangeError(`ttlMs must be zero or a positive number, got ${ttlMs}`);
  }
  const entries = new Map();
  const counters = { hits: 0, misses: 0, evictions: 0, expirations: 0 };

  const isExpired = (entry) => entry.expiresAt !== null && now() >= entry.expiresAt;

  function touch(key, entry) {
    entries.delete(key);
    entries.set(key, entry);
  }

  function get(key) {
    const entry = entries.get(key);
    if (entry === undefined) {
      counters.misses += 1;
      return undefined;
    }
    if (isExpired(entry)) {
      entries.delete(key);
      counters.expirations += 1;
      counters.misses += 1;
      return undefined;
    }
    touch(key, entry);
    counters.hits += 1;
    return entry.value;
  }

  function set(key, value, { ttlMs: override } = {}) {
    const effective = override === undefined ? ttlMs : override;
    if (!Number.isFinite(effective) || effective < 0) {
      throw new RangeError(`ttlMs must be zero or a positive number, got ${effective}`);
    }
    entries.delete(key);
    while (entries.size >= capacity) {
      const oldest = entries.keys().next();
      if (oldest.done) break;
      entries.delete(oldest.value);
      counters.evictions += 1;
    }
    entries.set(key, {
      value,
      expiresAt: effective > 0 ? now() + effective : null,
    });
  }

  function has(key) {
    const entry = entries.get(key);
    if (entry === undefined) return false;
    if (isExpired(entry)) {
      entries.delete(key);
      counters.expirations += 1;
      return false;
    }
    return true;
  }

  function remove(key) {
    return entries.delete(key);
  }

  function sweep() {
    let removed = 0;
    for (const [key, entry] of entries) {
      if (isExpired(entry)) {
        entries.delete(key);
        removed += 1;
      }
    }
    counters.expirations += removed;
    return removed;
  }

  return {
    get,
    set,
    has,
    delete: remove,
    clear() {
      entries.clear();
    },
    sweep,
    get size() {
      return entries.size;
    },
    keys() {
      return [...entries.keys()];
    },
    stats() {
      return {
        ...counters,
        entries: entries.size,
        capacity,
        ttlMs,
        hitRate: counters.hits + counters.misses === 0
          ? 0
          : counters.hits / (counters.hits + counters.misses),
      };
    },
  };
}
