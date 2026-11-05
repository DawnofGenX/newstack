//! HTTP layer. Every error body is a struct (serde emits fields in declaration
//! order), and routing is done by hand so 405/404 answers are ours, not axum's.

use axum::body::Bytes;
use axum::extract::State;
use axum::http::{Method, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::routing::any;
use axum::{Json, Router};
use serde::Serialize;

use crate::store::{normalise_title, Note, Store, StoreError};

#[derive(Serialize)]
struct ErrorBody {
    error: &'static str,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail: Option<String>,
}

#[derive(Serialize)]
struct NoteList {
    notes: Vec<Note>,
}

#[derive(Serialize)]
struct Health {
    status: &'static str,
    notes: i64,
}

fn error(status: StatusCode, kind: &'static str, detail: Option<String>) -> Response {
    (
        status,
        Json(ErrorBody {
            error: kind,
            detail,
        }),
    )
        .into_response()
}

fn not_found_note(id: i64) -> Response {
    error(
        StatusCode::NOT_FOUND,
        "not_found",
        Some(format!("no note with id {id}")),
    )
}

fn route_not_found(method: &Method, path: &str) -> Response {
    error(
        StatusCode::NOT_FOUND,
        "not_found",
        Some(format!("no route for {method} {path}")),
    )
}

fn method_not_allowed() -> Response {
    error(StatusCode::METHOD_NOT_ALLOWED, "method_not_allowed", None)
}

fn invalid_request(detail: &str) -> Response {
    error(
        StatusCode::UNPROCESSABLE_ENTITY,
        "invalid_request",
        Some(detail.to_string()),
    )
}

fn invalid_json() -> Response {
    error(StatusCode::UNPROCESSABLE_ENTITY, "invalid_json", None)
}

pub fn router(store: Store) -> Router {
    Router::new()
        .route("/health", any(health_or_405))
        .route("/notes", any(notes_collection))
        .route("/notes/{id}", any(notes_item))
        .fallback(unknown_route)
        .with_state(store)
}

async fn health_or_405(State(store): State<Store>, method: Method) -> Response {
    if method != Method::GET {
        return method_not_allowed();
    }
    match store.count().await {
        Ok(notes) => (
            StatusCode::OK,
            Json(Health {
                status: "ok",
                notes,
            }),
        )
            .into_response(),
        Err(err) => internal(err),
    }
}

/// `GET /notes` lists, `POST /notes` creates. Anything else is our own 405.
async fn notes_collection(State(store): State<Store>, method: Method, body: Bytes) -> Response {
    match method {
        Method::GET => match store.list().await {
            Ok(notes) => (StatusCode::OK, Json(NoteList { notes })).into_response(),
            Err(err) => internal(err),
        },
        Method::POST => {
            let text = match std::str::from_utf8(&body) {
                Ok(text) => text,
                Err(_) => return invalid_json(),
            };
            let value: serde_json::Value = match serde_json::from_str(text) {
                Ok(value) => value,
                Err(_) => return invalid_json(),
            };
            let Some(object) = value.as_object() else {
                return invalid_json();
            };
            let title = match object.get("title") {
                Some(serde_json::Value::String(raw)) => match normalise_title(raw) {
                    Some(title) => title,
                    None => return invalid_request("title: must not be blank"),
                },
                Some(_) => return invalid_request("title: must be a string"),
                None => return invalid_request("title: is required"),
            };
            let body_text = match object.get("body") {
                None | Some(serde_json::Value::Null) => String::new(),
                Some(serde_json::Value::String(raw)) => raw.clone(),
                Some(_) => return invalid_request("body: must be a string"),
            };
            match store.create(&title, &body_text).await {
                Ok(note) => (StatusCode::CREATED, Json(note)).into_response(),
                Err(err) => internal(err),
            }
        }
        _ => method_not_allowed(),
    }
}

/// `/notes/{id}`: GET, PATCH, DELETE. The path id is parsed here so a
/// non-numeric id is a 404 on the route (there is no such note), not a 400.
async fn notes_item(
    State(store): State<Store>,
    method: Method,
    axum::extract::Path(raw): axum::extract::Path<String>,
    body: Bytes,
) -> Response {
    let Ok(id) = raw.parse::<i64>() else {
        return route_not_found(&method, &format!("/notes/{raw}"));
    };
    match method {
        Method::GET => match store.get(id).await {
            Ok(note) => (StatusCode::OK, Json(note)).into_response(),
            Err(StoreError::NotFound(_)) => not_found_note(id),
            Err(StoreError::Db(err)) => internal(err),
        },
        Method::PATCH => {
            let text = match std::str::from_utf8(&body) {
                Ok(text) => text,
                Err(_) => return invalid_json(),
            };
            let value: serde_json::Value = match serde_json::from_str(text) {
                Ok(value) => value,
                Err(_) => return invalid_json(),
            };
            let Some(object) = value.as_object() else {
                return invalid_json();
            };
            let mut title: Option<String> = None;
            if let Some(raw_title) = object.get("title") {
                match raw_title {
                    serde_json::Value::String(text) => match normalise_title(text) {
                        Some(clean) => title = Some(clean),
                        None => return invalid_request("title: must not be blank"),
                    },
                    _ => return invalid_request("title: must be a string"),
                }
            }
            let mut body_text: Option<String> = None;
            if let Some(raw_body) = object.get("body") {
                match raw_body {
                    serde_json::Value::String(text) => body_text = Some(text.clone()),
                    _ => return invalid_request("body: must be a string"),
                }
            }
            if title.is_none() && body_text.is_none() {
                return invalid_request("patch: needs a title or a body");
            }
            match store
                .patch(id, title.as_deref(), body_text.as_deref())
                .await
            {
                Ok(note) => (StatusCode::OK, Json(note)).into_response(),
                Err(StoreError::NotFound(_)) => not_found_note(id),
                Err(StoreError::Db(err)) => internal(err),
            }
        }
        Method::DELETE => match store.delete(id).await {
            Ok(()) => StatusCode::NO_CONTENT.into_response(),
            Err(StoreError::NotFound(_)) => not_found_note(id),
            Err(StoreError::Db(err)) => internal(err),
        },
        _ => method_not_allowed(),
    }
}

async fn unknown_route(method: Method, uri: axum::http::Uri) -> Response {
    route_not_found(&method, uri.path())
}

fn internal(err: sqlx::Error) -> Response {
    eprintln!("store error: {err}");
    error(StatusCode::INTERNAL_SERVER_ERROR, "internal_error", None)
}
