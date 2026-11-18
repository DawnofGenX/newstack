use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread::sleep;
use std::time::Duration;

use {{ package_name }}::JobQueue;

fn main() {
    let n: usize = std::env::args()
        .nth(1)
        .and_then(|s| s.parse().ok())
        .unwrap_or(4);
    let attempts = std::env::args()
        .nth(2)
        .and_then(|s| s.parse().ok())
        .unwrap_or(3);

    let counter = Arc::new(AtomicUsize::new(0));
    let mut q = JobQueue::new(n, attempts);
    for i in 0..n {
        let c = Arc::clone(&counter);
        q.submit(move || {
            sleep(Duration::from_millis(10));
            c.fetch_add(1, Ordering::SeqCst);
            Ok(())
        });
        let _ = i;
    }
    // collect
    for _ in 0..n {
        if let Some(r) = q.recv_result_timeout(Duration::from_secs(5)) {
            println!("job ok={} attempts={}", r.ok, r.attempts);
        }
    }
    q.shutdown();
}
