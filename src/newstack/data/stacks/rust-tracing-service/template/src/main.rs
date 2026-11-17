use std::{env, error::Error, net::SocketAddr};

use tokio::net::TcpListener;

const DEFAULT_PORT: u16 = 5514;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    {{ package_name }}::init_tracing();
    let port = match env::var("PORT") {
        Ok(value) => value
            .parse::<u16>()
            .map_err(|_| format!("PORT must be a number between 0 and 65535, got {value:?}"))?,
        Err(_) => DEFAULT_PORT,
    };

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    let listener = TcpListener::bind(addr).await?;
    tracing::info!(%addr, "listening");
    axum::serve(listener, {{ package_name }}::app())
        .with_graceful_shutdown(shutdown_signal())
        .await?;
    tracing::info!("shutdown complete");
    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("failed to install SIGTERM handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        () = ctrl_c => {},
        () = terminate => {},
    }
    tracing::info!("shutdown signal received");
}
