package {{ package_name }};

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * A fixed-capacity least-recently-used cache.
 *
 * <p>The recency order is kept in a doubly linked list with sentinels, so
 * {@link #get(Object)} is O(1) and never scans the index. {@link #peek(Object)}
 * reads without touching the order or the counters, which is what a monitoring
 * endpoint wants.
 */
public final class LruCache<K, V> {

    /** A node in the recency list. */
    private static final class Node<K, V> {
        K key;
        V value;
        Node<K, V> previous;
        Node<K, V> next;
    }

    /** A snapshot of the counters. */
    public record Stats(long hits, long misses, long evictions, int size, int capacity) {
        /** Share of lookups that found a value, in the range 0..1. */
        public double hitRate() {
            long lookups = hits + misses;
            return lookups == 0 ? 0.0 : (double) hits / lookups;
        }
    }

    private final int capacity;
    private final Map<K, Node<K, V>> index = new HashMap<>();
    private final Node<K, V> head = new Node<>();
    private final Node<K, V> tail = new Node<>();
    private long hits;
    private long misses;
    private long evictions;

    public LruCache(int capacity) {
        if (capacity < 1) {
            throw new IllegalArgumentException("capacity must be at least 1, got " + capacity);
        }
        this.capacity = capacity;
        head.next = tail;
        tail.previous = head;
    }

    /** Returns the value for {@code key}, marking it most recently used. */
    public Optional<V> get(K key) {
        Node<K, V> found = index.get(key);
        if (found == null) {
            misses++;
            return Optional.empty();
        }
        hits++;
        unlink(found);
        linkFirst(found);
        return Optional.of(found.value);
    }

    /** Returns the value for {@code key} without changing order or counters. */
    public Optional<V> peek(K key) {
        Node<K, V> found = index.get(key);
        return found == null ? Optional.empty() : Optional.of(found.value);
    }

    /**
     * Stores a value, returning the evicted key when the cache had to make room.
     */
    public Optional<K> put(K key, V value) {
        Node<K, V> found = index.get(key);
        if (found != null) {
            found.value = value;
            unlink(found);
            linkFirst(found);
            return Optional.empty();
        }
        Node<K, V> node = new Node<>();
        node.key = key;
        node.value = value;
        index.put(key, node);
        linkFirst(node);
        if (index.size() <= capacity) {
            return Optional.empty();
        }
        Node<K, V> victim = tail.previous;
        unlink(victim);
        index.remove(victim.key);
        evictions++;
        return Optional.of(victim.key);
    }

    /** Removes {@code key} if present and returns whether anything was removed. */
    public boolean remove(K key) {
        Node<K, V> found = index.remove(key);
        if (found == null) {
            return false;
        }
        unlink(found);
        return true;
    }

    public boolean contains(K key) {
        return index.containsKey(key);
    }

    public int size() {
        return index.size();
    }

    public int capacity() {
        return capacity;
    }

    /** Keys ordered from most to least recently used. */
    public List<K> keys() {
        List<K> keys = new ArrayList<>(index.size());
        for (Node<K, V> node = head.next; node != tail; node = node.next) {
            keys.add(node.key);
        }
        return keys;
    }

    /** Empties the cache and resets the counters. */
    public void clear() {
        index.clear();
        head.next = tail;
        tail.previous = head;
        hits = 0;
        misses = 0;
        evictions = 0;
    }

    public Stats stats() {
        return new Stats(hits, misses, evictions, index.size(), capacity);
    }

    private void linkFirst(Node<K, V> node) {
        node.previous = head;
        node.next = head.next;
        head.next.previous = node;
        head.next = node;
    }

    private void unlink(Node<K, V> node) {
        node.previous.next = node.next;
        node.next.previous = node.previous;
        node.previous = null;
        node.next = null;
    }
}
