package {{ package_name }};

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class VirtualClock implements Clock {
    private long now;
    void advance(long ms) { now += ms; }
    public long nowMillis() { return now; }
}

class RateLimiterTest {
    @Test
    void allowsUpToCapacity() {
        VirtualClock c = new VirtualClock();
        RateLimiter rl = new RateLimiter(3, 1, c);
        assertTrue(rl.tryAcquire());
        assertTrue(rl.tryAcquire());
        assertTrue(rl.tryAcquire());
        assertFalse(rl.tryAcquire());
    }

    @Test
    void refillsOverTime() {
        VirtualClock c = new VirtualClock();
        RateLimiter rl = new RateLimiter(2, 2, c); // 2 tokens/sec
        assertTrue(rl.tryAcquire());
        assertTrue(rl.tryAcquire());
        assertFalse(rl.tryAcquire());
        c.advance(1000);
        assertTrue(rl.tryAcquire());
        assertTrue(rl.tryAcquire());
        assertFalse(rl.tryAcquire());
    }

    @Test
    void tryAcquireN() {
        VirtualClock c = new VirtualClock();
        RateLimiter rl = new RateLimiter(5, 1, c);
        assertTrue(rl.tryAcquire(3));
        assertFalse(rl.tryAcquire(3));
        assertTrue(rl.tryAcquire(2));
    }
}
