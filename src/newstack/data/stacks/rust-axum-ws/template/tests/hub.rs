use std::time::Duration;

use {{ package_name }}::Hub;
use tokio::time::timeout;

#[tokio::test]
async fn broadcasts_to_all_subscribers() {
    let hub = Hub::new(16);
    let mut first = hub.subscribe();
    let mut second = hub.subscribe();

    assert_eq!(hub.broadcast("hello".to_owned()), 2);

    let received_first = timeout(Duration::from_secs(1), first.recv())
        .await
        .expect("first timed out")
        .expect("first closed");
    let received_second = timeout(Duration::from_secs(1), second.recv())
        .await
        .expect("second timed out")
        .expect("second closed");

    assert_eq!(received_first, "hello");
    assert_eq!(received_second, "hello");
}

#[tokio::test]
async fn subscriber_count_tracks_subscriptions() {
    let hub = Hub::new(16);
    let _rx = hub.subscribe();
    assert_eq!(hub.subscriber_count(), 1);
}
