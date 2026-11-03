//! Integration tests over the router itself — no socket, no port, no sleep.

use axum::{
    body::Body,
    http::{Request, StatusCode, header},
};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use tower::ServiceExt;

fn get(path: &str) -> Request<Body> {
    Request::builder()
        .uri(path)
        .body(Body::empty())
        .expect("request builds")
}

fn post_json(path: &str, body: &str) -> Request<Body> {
    Request::builder()
        .method("POST")
        .uri(path)
        .header(header::CONTENT_TYPE, "application/json")
        .body(Body::from(body.to_owned()))
        .expect("request builds")
}

async fn body_json(response: axum::response::Response) -> Value {
    let bytes = response
        .into_body()
        .collect()
        .await
        .expect("body collects")
        .to_bytes();
    serde_json::from_slice(&bytes).expect("body is JSON")
}

#[tokio::test]
async fn health_reports_ok() {
    let response = {{ package_name }}::app()
        .oneshot(get("/health"))
        .await
        .expect("router responds");

    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(body_json(response).await, json!({"status": "ok"}));
}

#[tokio::test]
async fn items_start_empty() {
    let response = {{ package_name }}::app()
        .oneshot(get("/items"))
        .await
        .expect("router responds");

    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(body_json(response).await, json!([]));
}

#[tokio::test]
async fn created_item_is_listed() {
    // Cloning the router clones the state handle, so both calls share one store.
    let app = {{ package_name }}::app();

    let created = app
        .clone()
        .oneshot(post_json("/items", r#"{"name":"widget"}"#))
        .await
        .expect("router responds");

    assert_eq!(created.status(), StatusCode::CREATED);
    assert_eq!(body_json(created).await, json!({"id": 1, "name": "widget"}));

    let listed = app.oneshot(get("/items")).await.expect("router responds");

    assert_eq!(listed.status(), StatusCode::OK);
    assert_eq!(
        body_json(listed).await,
        json!([{"id": 1, "name": "widget"}])
    );
}

#[tokio::test]
async fn malformed_json_is_bad_request() {
    let response = {{ package_name }}::app()
        .oneshot(post_json("/items", r#"{"name":"#))
        .await
        .expect("router responds");

    assert_eq!(response.status(), StatusCode::BAD_REQUEST);
}

#[tokio::test]
async fn missing_field_is_bad_request() {
    let response = {{ package_name }}::app()
        .oneshot(post_json("/items", r#"{}"#))
        .await
        .expect("router responds");

    assert_eq!(response.status(), StatusCode::BAD_REQUEST);
}
