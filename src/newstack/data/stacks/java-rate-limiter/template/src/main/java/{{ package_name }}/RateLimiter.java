package {{ package_name }};

public class RateLimiter {
    private final long capacity;
    private final long refillPerSecond;
    private long tokens;
    private long lastRefill;
    private final Clock clock;

    public RateLimiter(long capacity, long refillPerSecond, Clock clock) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity");
        if (refillPerSecond < 0) throw new IllegalArgumentException("refill");
        this.capacity = capacity;
        this.refillPerSecond = refillPerSecond;
        this.clock = clock;
        this.tokens = capacity;
        this.lastRefill = clock.nowMillis();
    }

    private void refill() {
        long now = clock.nowMillis();
        long delta = now - lastRefill;
        if (delta < 0) delta = 0;
        long add = delta * refillPerSecond / 1000L;
        tokens = Math.min(capacity, tokens + add);
        lastRefill = now;
    }

    public synchronized boolean tryAcquire() {
        return tryAcquire(1);
    }

    public synchronized boolean tryAcquire(int n) {
        if (n <= 0) return true;
        refill();
        if (tokens >= n) {
            tokens -= n;
            return true;
        }
        return false;
    }

    public synchronized long available() {
        refill();
        return tokens;
    }
}
