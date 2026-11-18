use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread::sleep;
use std::time::Duration;

use {{ package_name }}::JobQueue;

#[test]
fn retry_exhaustion() {
    let mut q = JobQueue::new(2, 3);
    q.submit(|| Err("boom".to_string()));
    let r = q.recv_result_timeout(Duration::from_secs(5)).unwrap();
    assert!(!r.ok);
    assert_eq!(r.attempts, 3);
    assert_eq!(r.error.as_deref(), Some("boom"));
    q.shutdown();
}

#[test]
fn success_first_attempt() {
    let mut q = JobQueue::new(2, 3);
    let c = Arc::new(AtomicUsize::new(0));
    let c2 = Arc::clone(&c);
    q.submit(move || {
        c2.fetch_add(1, Ordering::SeqCst);
        Ok(())
    });
    let r = q.recv_result_timeout(Duration::from_secs(5)).unwrap();
    assert!(r.ok);
    assert_eq!(r.attempts, 1);
    assert_eq!(c.load(Ordering::SeqCst), 1);
    q.shutdown();
}

#[test]
fn shutdown_rejects_no_crash() {
    let mut q = JobQueue::new(2, 2);
    q.shutdown();
    // after shutdown submit is no-op; no panic
    q.submit(|| Ok(()));
    assert!(q.is_shutdown());
}
