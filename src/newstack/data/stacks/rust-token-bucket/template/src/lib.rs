//! A token bucket rate limiter with an injectable millisecond clock.

/// A token bucket that refills at a fixed rate and never exceeds its capacity.
#[derive(Debug, Clone)]
pub struct TokenBucket {
    capacity: f64,
    tokens: f64,
    refill_per_second: f64,
    last_ms: u64,
}

impl TokenBucket {
    /// Creates a full bucket whose clock starts at `now_ms`.
    pub fn new(capacity: u64, refill_per_second: f64, now_ms: u64) -> Self {
        assert!(capacity > 0, "capacity must be positive");
        assert!(
            refill_per_second > 0.0,
            "refill rate must be positive to make progress"
        );
        Self {
            capacity: capacity as f64,
            tokens: capacity as f64,
            refill_per_second,
            last_ms: now_ms,
        }
    }

    /// Adds the tokens earned since the previous call and clamps to capacity.
    pub fn refill(&mut self, now_ms: u64) {
        if now_ms <= self.last_ms {
            return;
        }
        let elapsed_ms = (now_ms - self.last_ms) as f64;
        let gained = self.refill_per_second * elapsed_ms / 1000.0;
        self.tokens = (self.tokens + gained).min(self.capacity);
        self.last_ms = now_ms;
    }

    /// Whole tokens available right now, after refilling.
    pub fn available(&mut self, now_ms: u64) -> u64 {
        self.refill(now_ms);
        self.tokens.floor() as u64
    }

    /// Takes `count` tokens if they are available, otherwise changes nothing.
    pub fn try_acquire_n(&mut self, count: u64, now_ms: u64) -> bool {
        if count == 0 {
            return true;
        }
        self.refill(now_ms);
        let want = count as f64;
        if self.tokens + f64::EPSILON >= want {
            self.tokens -= want;
            true
        } else {
            false
        }
    }

    /// Takes a single token if one is available.
    pub fn try_acquire(&mut self, now_ms: u64) -> bool {
        self.try_acquire_n(1, now_ms)
    }

    /// Milliseconds until `count` whole tokens can be taken.
    pub fn time_until(&mut self, count: u64, now_ms: u64) -> Option<u64> {
        if count == 0 {
            return Some(0);
        }
        let want = count as f64;
        if want > self.capacity + f64::EPSILON {
            return None;
        }
        self.refill(now_ms);
        if self.tokens + f64::EPSILON >= want {
            return Some(0);
        }
        let missing = want - self.tokens;
        let ms = (missing / self.refill_per_second * 1000.0).ceil();
        Some(ms.max(0.0) as u64)
    }
}
