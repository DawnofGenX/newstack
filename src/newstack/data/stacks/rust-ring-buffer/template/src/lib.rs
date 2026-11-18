use std::collections::VecDeque;

#[derive(Debug, Clone)]
pub struct RingBuffer<T> {
    capacity: usize,
    data: VecDeque<T>,
}

impl<T> RingBuffer<T> {
    pub fn new(capacity: usize) -> Self {
        Self {
            capacity,
            data: VecDeque::with_capacity(capacity),
        }
    }

    pub fn capacity(&self) -> usize {
        self.capacity
    }

    pub fn len(&self) -> usize {
        self.data.len()
    }

    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    pub fn is_full(&self) -> bool {
        self.capacity > 0 && self.data.len() == self.capacity
    }

    pub fn push(&mut self, value: T) {
        if self.capacity == 0 {
            return;
        }
        if self.data.len() == self.capacity {
            self.data.pop_front();
        }
        self.data.push_back(value);
    }

    pub fn pop(&mut self) -> Option<T> {
        self.data.pop_front()
    }

    pub fn front(&self) -> Option<&T> {
        self.data.front()
    }

    pub fn back(&self) -> Option<&T> {
        self.data.back()
    }

    pub fn get(&self, index: usize) -> Option<&T> {
        self.data.get(index)
    }

    pub fn clear(&mut self) {
        self.data.clear();
    }

    pub fn iter(&self) -> impl Iterator<Item = &T> {
        self.data.iter()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn push_and_len() {
        let mut r = RingBuffer::new(3);
        r.push(1);
        r.push(2);
        assert_eq!(r.len(), 2);
        assert!(!r.is_full());
        assert_eq!(r.front(), Some(&1));
        assert_eq!(r.back(), Some(&2));
    }

    #[test]
    fn overwrites_oldest() {
        let mut r = RingBuffer::new(3);
        for v in 1..=5 {
            r.push(v);
        }
        assert_eq!(r.len(), 3);
        assert!(r.is_full());
        let vals: Vec<_> = r.iter().copied().collect();
        assert_eq!(vals, vec![3, 4, 5]);
    }

    #[test]
    fn pop_front() {
        let mut r = RingBuffer::new(2);
        r.push(10);
        r.push(20);
        assert_eq!(r.pop(), Some(10));
        assert_eq!(r.pop(), Some(20));
        assert_eq!(r.pop(), None);
    }

    #[test]
    fn get_by_index() {
        let mut r = RingBuffer::new(4);
        r.push(7);
        r.push(8);
        assert_eq!(r.get(0), Some(&7));
        assert_eq!(r.get(1), Some(&8));
        assert_eq!(r.get(2), None);
    }

    #[test]
    fn capacity_zero_ignores_push() {
        let mut r = RingBuffer::new(0);
        r.push(1);
        assert!(r.is_empty());
        assert_eq!(r.len(), 0);
    }

    #[test]
    fn clear() {
        let mut r = RingBuffer::new(2);
        r.push(1);
        r.push(2);
        r.clear();
        assert!(r.is_empty());
    }
}
