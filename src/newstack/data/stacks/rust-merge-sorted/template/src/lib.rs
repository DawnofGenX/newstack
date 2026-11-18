//! K-way merge of pre-sorted integer streams.

use std::cmp::Reverse;
use std::collections::BinaryHeap;

/// True when every element is greater than or equal to its predecessor.
pub fn is_sorted(values: &[i64]) -> bool {
    values.windows(2).all(|w| w[0] <= w[1])
}

/// Parses one integer per line, skipping blank lines.
pub fn parse_block(text: &str) -> Result<Vec<i64>, String> {
    let mut out = Vec::new();
    for (index, raw) in text.lines().enumerate() {
        let trimmed = raw.trim();
        if trimmed.is_empty() {
            continue;
        }
        match trimmed.parse::<i64>() {
            Ok(value) => out.push(value),
            Err(_) => return Err(format!("line {} is not an integer: {trimmed:?}", index + 1)),
        }
    }
    Ok(out)
}

/// Merges any number of ascending runs into one ascending run.
///
/// Each input is walked once, so the cost is `n log k` comparisons for `n`
/// total elements across `k` runs regardless of how many runs are empty.
pub fn merge_sorted(inputs: &[Vec<i64>]) -> Vec<i64> {
    let total: usize = inputs.iter().map(|run| run.len()).sum();
    let mut merged = Vec::with_capacity(total);
    // (value, which run, position inside that run) kept as a min-heap.
    let mut heap: BinaryHeap<Reverse<(i64, usize, usize)>> = BinaryHeap::new();
    for (run_index, run) in inputs.iter().enumerate() {
        if let Some(first) = run.first() {
            heap.push(Reverse((*first, run_index, 0)));
        }
    }
    while let Some(Reverse((value, run_index, position))) = heap.pop() {
        merged.push(value);
        let next = position + 1;
        if let Some(more) = inputs[run_index].get(next) {
            heap.push(Reverse((*more, run_index, next)));
        }
    }
    merged
}
