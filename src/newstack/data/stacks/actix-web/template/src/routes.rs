//! HTTP handlers only: wrap the pure `contract::dispatch` reply into an
//! actix HttpResponse. Routes register `web::route()` (any method) so that
//! wrong-method replies are our JSON (`{"error":"method_not_allowed"}`),
//! not actix's default plain-text 405.

use actix_web::http::StatusCode;
use actix_web::{web, HttpRequest, HttpResponse};

use crate::contract::{dispatch, Reply};

fn to_http(reply: Reply) -> HttpResponse {
    HttpResponse::build(
        StatusCode::from_u16(reply.status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
    )
    .content_type("application/json")
    .body(reply.body)
}

/// Any-method handler for /health and /stats; dispatch decides everything.
pub async fn handler(req: HttpRequest, body: web::Bytes) -> HttpResponse {
    let payload = if req.method() == actix_web::http::Method::POST {
        Some(body.to_vec())
    } else {
        None
    };
    to_http(dispatch(
        req.method().as_str(),
        req.path(),
        req.query_string(),
        payload.as_deref(),
    ))
}

/// Catch-all for unknown paths -> 404 with the exact detail string.
pub async fn not_found(req: HttpRequest) -> HttpResponse {
    to_http(dispatch(
        req.method().as_str(),
        req.path(),
        req.query_string(),
        None,
    ))
}
