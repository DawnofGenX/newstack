use {{ package_name }}::TokenBucket;

#[test]
fn burst_within_capacity_is_allowed() {
    let mut bucket = TokenBucket::new(3, 1.0, 0);
    assert!(bucket.try_acquire(0));
    assert!(bucket.try_acquire(0));
    assert!(bucket.try_acquire(0));
    assert!(
        !bucket.try_acquire(0),
        "fourth request in the burst must fail"
    );
}

#[test]
fn refill_restores_tokens_over_time() {
    let mut bucket = TokenBucket::new(2, 2.0, 0);
    assert!(bucket.try_acquire_n(2, 0));
    assert_eq!(bucket.available(0), 0);
    assert_eq!(bucket.available(499), 0, "half a token is not a token yet");
    assert_eq!(bucket.available(500), 1);
    assert_eq!(bucket.available(1000), 2);
}

#[test]
fn refill_never_exceeds_capacity() {
    let mut bucket = TokenBucket::new(4, 100.0, 0);
    assert_eq!(bucket.available(60_000), 4);
    assert_eq!(bucket.available(120_000), 4);
}

#[test]
fn partial_tokens_accumulate_across_calls() {
    let mut bucket = TokenBucket::new(1, 1.0, 0);
    assert!(bucket.try_acquire(0));
    // 300ms twice is 0.6 tokens: not enough, but the remaining capacity is kept.
    assert_eq!(bucket.available(300), 0);
    assert_eq!(bucket.available(600), 0);
    assert_eq!(bucket.available(1000), 1);
}

#[test]
fn acquire_n_is_all_or_nothing() {
    let mut bucket = TokenBucket::new(3, 1.0, 0);
    assert!(!bucket.try_acquire_n(4, 0));
    assert_eq!(bucket.available(0), 3);
    assert!(bucket.try_acquire_n(3, 0));
    assert_eq!(bucket.available(0), 0);
    assert!(bucket.try_acquire_n(0, 0), "zero tokens always succeeds");
}

#[test]
fn time_until_reports_the_wait() {
    let mut bucket = TokenBucket::new(2, 1.0, 0);
    assert!(bucket.try_acquire_n(2, 0));
    assert_eq!(bucket.time_until(1, 0), Some(1000));
    assert_eq!(bucket.time_until(2, 0), Some(2000));
    assert_eq!(
        bucket.time_until(9, 0),
        None,
        "more than capacity is unreachable"
    );
    assert_eq!(bucket.time_until(0, 0), Some(0));
}

#[test]
fn clock_going_backwards_is_ignored() {
    let mut bucket = TokenBucket::new(2, 1.0, 1000);
    assert!(bucket.try_acquire(1000));
    assert_eq!(
        bucket.available(0),
        1,
        "an earlier timestamp must not refill"
    );
}
