pub mod routes;
pub mod selftest;
pub mod store;

use std::net::SocketAddr;

/// Bind and serve until the process is cancelled by a signal.
pub async fn run(store: store::Store, addr: &str) -> std::io::Result<()> {
    let app = routes::router(store);
    let parsed: SocketAddr = addr
        .parse()
        .map_err(|err| std::io::Error::new(std::io::ErrorKind::InvalidInput, format!("{err}")))?;
    let listener = tokio::net::TcpListener::bind(parsed).await?;
    println!("listening on http://{parsed}");
    axum::serve(listener, app)
        .with_graceful_shutdown(async {
            let _ = tokio::signal::ctrl_c().await;
        })
        .await
}
