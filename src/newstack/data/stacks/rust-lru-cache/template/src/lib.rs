use std::collections::{HashMap, VecDeque};
use std::hash::Hash;

#[derive(Debug)]
pub struct LruCache<K, V> {
    capacity: usize,
    map: HashMap<K, V>,
    order: VecDeque<K>,
}

impl<K, V> LruCache<K, V>
where
    K: Clone + Eq + Hash,
{
    pub fn new(capacity: usize) -> Self {
        Self {
            capacity,
            map: HashMap::new(),
            order: VecDeque::new(),
        }
    }

    pub fn capacity(&self) -> usize {
        self.capacity
    }

    pub fn len(&self) -> usize {
        self.map.len()
    }

    pub fn is_empty(&self) -> bool {
        self.map.is_empty()
    }

    pub fn get(&mut self, key: &K) -> Option<&V> {
        if self.map.contains_key(key) {
            self.touch(key);
            self.map.get(key)
        } else {
            None
        }
    }

    pub fn peek(&self, key: &K) -> Option<&V> {
        self.map.get(key)
    }

    pub fn put(&mut self, key: K, value: V) {
        if self.capacity == 0 {
            return;
        }
        if self.map.contains_key(&key) {
            self.map.insert(key.clone(), value);
            self.touch(&key);
            return;
        }
        if self.map.len() >= self.capacity
            && let Some(evicted) = self.order.pop_front()
        {
            self.map.remove(&evicted);
        }
        self.map.insert(key.clone(), value);
        self.order.push_back(key);
    }

    fn touch(&mut self, key: &K) {
        if let Some(pos) = self.order.iter().position(|k| k == key) {
            self.order.remove(pos);
        }
        self.order.push_back(key.clone());
    }

    pub fn contains(&self, key: &K) -> bool {
        self.map.contains_key(key)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic_get_put() {
        let mut c = LruCache::new(2);
        c.put(1, "a");
        c.put(2, "b");
        assert_eq!(c.get(&1), Some(&"a"));
        assert_eq!(c.get(&2), Some(&"b"));
    }

    #[test]
    fn eviction_order() {
        let mut c = LruCache::new(2);
        c.put(1, "a");
        c.put(2, "b");
        c.put(3, "c");
        assert!(!c.contains(&1));
        assert_eq!(c.get(&2), Some(&"b"));
        assert_eq!(c.get(&3), Some(&"c"));
    }

    #[test]
    fn lru_touch_on_get() {
        let mut c = LruCache::new(2);
        c.put(1, "a");
        c.put(2, "b");
        assert_eq!(c.get(&1), Some(&"a"));
        c.put(3, "c");
        assert!(!c.contains(&2));
        assert!(c.contains(&1));
    }

    #[test]
    fn peek_does_not_touch() {
        let mut c = LruCache::new(2);
        c.put(1, "a");
        c.put(2, "b");
        assert_eq!(c.peek(&1), Some(&"a"));
        c.put(3, "c");
        assert!(!c.contains(&1));
    }

    #[test]
    fn capacity_zero() {
        let mut c = LruCache::new(0);
        c.put(1, "a");
        assert!(c.is_empty());
        assert_eq!(c.get(&1), None);
    }

    #[test]
    fn update_existing() {
        let mut c = LruCache::new(2);
        c.put(1, "a");
        c.put(1, "aa");
        assert_eq!(c.get(&1), Some(&"aa"));
        assert_eq!(c.len(), 1);
    }
}
