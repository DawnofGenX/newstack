use std::thread::sleep;
use std::time::{Duration, Instant};

use {{ package_name }}::ThreadPool;

#[test]
fn results_are_collected() {
    let mut pool = ThreadPool::new(2);
    let rx = pool.submit(|| 42).expect("submit");
    assert_eq!(rx.recv().expect("recv"), 42);
    pool.shutdown();
}

#[test]
fn parallelism() {
    let mut pool = ThreadPool::new(4);
    let start = Instant::now();
    let mut rxs = Vec::new();
    for _ in 0..4 {
        rxs.push(
            pool.submit(|| {
                sleep(Duration::from_millis(100));
                1
            })
            .expect("submit"),
        );
    }
    for rx in rxs {
        assert_eq!(rx.recv().expect("recv"), 1);
    }
    assert!(start.elapsed() < Duration::from_millis(250));
    pool.shutdown();
}

#[test]
fn shutdown_rejects_later_submissions() {
    let mut pool = ThreadPool::new(2);
    pool.shutdown();
    assert!(pool.submit(|| 1).is_err());
}
