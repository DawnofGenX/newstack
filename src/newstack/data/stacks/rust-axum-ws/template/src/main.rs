use std::net::SocketAddr;

use axum::Router;
use axum::extract::State;
use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::response::IntoResponse;
use axum::routing::get;
use {{ package_name }}::Hub;
use futures_util::SinkExt;
use futures_util::StreamExt;
use tokio::net::TcpListener;

async fn health() -> &'static str {
    "ok"
}

async fn ws_handler(ws: WebSocketUpgrade, State(hub): State<Hub>) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, hub))
}

async fn handle_socket(socket: WebSocket, hub: Hub) {
    let (mut sender, mut receiver) = socket.split();
    let mut broadcast_rx = hub.subscribe();

    let send_task = tokio::spawn(async move {
        while let Ok(message) = broadcast_rx.recv().await {
            if sender.send(Message::Text(message.into())).await.is_err() {
                break;
            }
        }
    });

    while let Some(Ok(message)) = receiver.next().await {
        if let Message::Text(text) = message {
            hub.broadcast(text.to_string());
        }
    }

    send_task.abort();
}

#[tokio::main]
async fn main() {
    let hub = Hub::new(1024);
    let app = Router::new()
        .route("/health", get(health))
        .route("/ws", get(ws_handler))
        .with_state(hub);

    let addr: SocketAddr = "0.0.0.0:5552".parse().unwrap();
    let listener = TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
