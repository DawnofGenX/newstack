package {{ package_name }};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.Test;

class LruCacheTest {

    @Test
    void evictsTheLeastRecentlyUsedEntry() {
        LruCache<String, Integer> cache = new LruCache<>(2);
        cache.put("a", 1);
        cache.put("b", 2);
        cache.get("a");
        assertEquals(Optional.of("b"), cache.put("c", 3));
        assertTrue(cache.contains("a"));
        assertFalse(cache.contains("b"));
    }

    @Test
    void keysAreOrderedMostRecentFirst() {
        LruCache<String, Integer> cache = new LruCache<>(3);
        cache.put("a", 1);
        cache.put("b", 2);
        cache.put("c", 3);
        cache.get("a");
        assertEquals(List.of("a", "c", "b"), cache.keys());
    }

    @Test
    void peekDoesNotChangeOrderOrCounters() {
        LruCache<String, Integer> cache = new LruCache<>(2);
        cache.put("a", 1);
        cache.put("b", 2);
        assertEquals(Optional.of(1), cache.peek("a"));
        assertEquals(List.of("b", "a"), cache.keys());
        assertEquals(0, cache.stats().hits());
        assertEquals(0, cache.stats().misses());
    }

    @Test
    void countersTrackHitsAndMisses() {
        LruCache<String, Integer> cache = new LruCache<>(2);
        cache.put("a", 1);
        cache.get("a");
        cache.get("zz");
        LruCache.Stats stats = cache.stats();
        assertEquals(1, stats.hits());
        assertEquals(1, stats.misses());
        assertEquals(0.5, stats.hitRate());
    }

    @Test
    void updatingAKeyDoesNotEvict() {
        LruCache<String, Integer> cache = new LruCache<>(2);
        cache.put("a", 1);
        cache.put("b", 2);
        assertEquals(Optional.empty(), cache.put("a", 9));
        assertEquals(2, cache.size());
        assertEquals(Optional.of(9), cache.get("a"));
        assertEquals(List.of("a", "b"), cache.keys());
    }

    @Test
    void getOnMissingKeyIsEmpty() {
        LruCache<String, Integer> cache = new LruCache<>(1);
        assertTrue(cache.get("nope").isEmpty());
    }

    @Test
    void removeReportsWhetherItRemovedAnything() {
        LruCache<String, Integer> cache = new LruCache<>(2);
        cache.put("a", 1);
        assertTrue(cache.remove("a"));
        assertFalse(cache.remove("a"));
    }

    @Test
    void clearResetsSizeAndCounters() {
        LruCache<String, Integer> cache = new LruCache<>(2);
        cache.put("a", 1);
        cache.get("a");
        cache.get("b");
        cache.clear();
        assertEquals(0, cache.size());
        assertEquals(0, cache.stats().hits());
        assertEquals(0, cache.stats().misses());
        assertTrue(cache.keys().isEmpty());
    }

    @Test
    void capacityMustBePositive() {
        assertThrows(IllegalArgumentException.class, () -> new LruCache<String, Integer>(0));
    }
}
