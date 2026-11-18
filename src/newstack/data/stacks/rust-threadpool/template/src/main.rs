use std::thread::sleep;
use std::time::Duration;

use {{ package_name }}::ThreadPool;

fn main() {
    let count: usize = std::env::args()
        .nth(1)
        .and_then(|s| s.parse().ok())
        .unwrap_or(4);

    let mut pool = ThreadPool::new(4);
    let mut receivers = Vec::with_capacity(count);
    for i in 0..count {
        let rx = pool
            .submit(move || {
                sleep(Duration::from_millis(50));
                i * i
            })
            .expect("submit failed");
        receivers.push(rx);
    }
    for rx in receivers {
        println!("{}", rx.recv().expect("recv failed"));
    }
    pool.shutdown();
}
