use std::net::TcpListener;

use {{ package_name }}::serve;
use {{ package_name }}::Store;
use std::sync::{Arc, Mutex};

fn main() {
    let port: u16 = std::env::args()
        .nth(1)
        .and_then(|s| s.parse().ok())
        .unwrap_or(5591);
    let listener = TcpListener::bind(format!("127.0.0.1:{}", port)).expect("bind failed");
    let store = Arc::new(Mutex::new(Store::new()));
    serve(listener, store);
}
