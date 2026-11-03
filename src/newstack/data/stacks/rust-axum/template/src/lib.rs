//! `Fmtprobe` — A Rust HTTP service.
//!
//! Routes are declared in [`app`], state is an `Arc<Mutex<Vec<Item>>>` handed to the
//! router with `with_state`, and every handler is a plain async function so the whole
//! surface can be exercised through `tower::ServiceExt::oneshot` without a socket.

use std::sync::{Arc, Mutex};

use axum::{Json, Router, extract::State, http::StatusCode, routing::get};
use serde::{Deserialize, Serialize};

/// One item in the collection.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Item {
    /// Server-assigned identifier, starting at 1.
    pub id: u64,
    /// Human-readable label.
    pub name: String,
}

/// Request body for `POST /items`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NewItem {
    /// Label for the new item.
    pub name: String,
}

/// Response body for `GET /health`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Health {
    /// Always `"ok"` while the process is serving.
    pub status: String,
}

/// Shared, thread-safe collection of items.
pub type AppState = Arc<Mutex<Vec<Item>>>;

/// An empty store, ready to be shared by the router.
pub fn new_state() -> AppState {
    Arc::new(Mutex::new(Vec::new()))
}

/// Router with a fresh, empty store.
pub fn app() -> Router {
    app_with_state(new_state())
}

/// Router over an existing store — lets tests seed or inspect state directly.
pub fn app_with_state(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/items", get(list_items).post(create_item))
        .with_state(state)
}

async fn health() -> Json<Health> {
    Json(Health {
        status: String::from("ok"),
    })
}

async fn list_items(State(state): State<AppState>) -> Json<Vec<Item>> {
    let items = {
        let guard = state.lock().expect("state mutex poisoned");
        guard.clone()
    };
    Json(items)
}

async fn create_item(
    State(state): State<AppState>,
    payload: Result<Json<NewItem>, axum::extract::rejection::JsonRejection>,
) -> Result<(StatusCode, Json<Item>), StatusCode> {
    // Normalising the extractor rejection keeps every bad body a 400, whether the
    // JSON failed to parse or a required field was missing (axum's default for the
    // latter is 422).
    let Json(new_item) = payload.map_err(|_| StatusCode::BAD_REQUEST)?;

    let item = {
        let mut guard = state.lock().expect("state mutex poisoned");
        let next_id = guard.iter().map(|item| item.id).max().unwrap_or(0) + 1;
        let item = Item {
            id: next_id,
            name: new_item.name,
        };
        guard.push(item.clone());
        item
    };

    Ok((StatusCode::CREATED, Json(item)))
}
