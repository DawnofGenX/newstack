use axum::{Json, Router, extract::State, routing::get};
use serde::Serialize;
use std::sync::{Arc, Mutex};

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Health {
    pub status: String,
}

pub type AppState = Arc<Mutex<u64>>;

pub fn new_state() -> AppState {
    Arc::new(Mutex::new(0))
}

pub fn app() -> Router {
    app_with_state(new_state())
}

pub fn app_with_state(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health))
        .with_state(state)
}

async fn health(State(state): State<AppState>) -> Json<Health> {
    let mut count = state.lock().expect("state mutex poisoned");
    *count += 1;
    tracing::info!(count = *count, "health check served");
    Json(Health {
        status: String::from("ok"),
    })
}

/// Initialize the global tracing subscriber with JSON output.
pub fn init_tracing() {
    use tracing_subscriber::{EnvFilter, fmt};
    let filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));
    fmt().json().with_env_filter(filter).init();
}
