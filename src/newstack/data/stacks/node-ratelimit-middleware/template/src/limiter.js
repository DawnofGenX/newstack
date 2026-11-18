export function createLimiter({ limit = 10, windowMs = 60000, now = () => Date.now() } = {}) {
  let windowStart = now();
  let count = 0;

  function resetIfNeeded(t) {
    if (t - windowStart >= windowMs) {
      windowStart = t;
      count = 0;
    }
  }

  return {
    tryAcquire() {
      const t = now();
      resetIfNeeded(t);
      if (count < limit) {
        count += 1;
        return { allowed: true, remaining: limit - count, retryAfter: 0 };
      }
      const retryAfter = Math.max(1, Math.ceil((windowStart + windowMs - t) / 1000));
      return { allowed: false, remaining: 0, retryAfter };
    },
    stats() {
      const t = now();
      resetIfNeeded(t);
      return {
        limit,
        windowMs,
        count,
        remaining: Math.max(0, limit - count),
        windowStart,
      };
    },
  };
}
