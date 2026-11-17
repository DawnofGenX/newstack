//! A JSON-RPC 2.0 server whose transport is stdin/stdout.
//!
//! One request per line in, at most one response per line out. This is the
//! shape every language server speaks, and the shape most people get wrong:
//! notifications are executed but never answered, batches get exactly one
//! array back, and the error codes are part of the spec rather than advice.

use std::collections::BTreeMap;

use serde::Deserialize;
use serde_json::{Value, json};

pub const PARSE_ERROR: i64 = -32700;
pub const INVALID_REQUEST: i64 = -32600;
pub const METHOD_NOT_FOUND: i64 = -32601;
pub const INVALID_PARAMS: i64 = -32602;

/// A spec error: a code from the reserved range, a message, and optional data.
#[derive(Debug, Clone)]
pub struct RpcError {
    pub code: i64,
    pub message: String,
    pub data: Option<Value>,
}

impl RpcError {
    pub fn new(code: i64, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
            data: None,
        }
    }

    pub fn with_data(code: i64, message: impl Into<String>, data: Value) -> Self {
        Self {
            code,
            message: message.into(),
            data: Some(data),
        }
    }

    pub fn to_value(&self) -> Value {
        let mut error = json!({ "code": self.code, "message": self.message });
        if let Some(data) = &self.data {
            error["data"] = data.clone();
        }
        error
    }
}

/// What arrives on a line. Every field is optional because a client that sends
/// `{"id":1}` has sent an invalid request, not a panic.
#[derive(Debug, Deserialize)]
struct RawRequest {
    #[serde(default)]
    jsonrpc: Option<String>,
    method: Option<String>,
    params: Option<Value>,
    #[serde(default)]
    id: Option<Value>,
}

pub fn error_response(id: Value, error: &RpcError) -> Value {
    json!({ "jsonrpc": "2.0", "id": id, "error": error.to_value() })
}

#[derive(Debug, Default)]
pub struct Dispatcher {
    notes: BTreeMap<String, String>,
    handled: u64,
}

impl Dispatcher {
    pub fn new() -> Self {
        Self::default()
    }

    /// Requests executed so far, notifications included.
    pub fn handled(&self) -> u64 {
        self.handled
    }

    /// One line in, at most one line out. `None` means "say nothing": a blank
    /// line, or a notification the client does not want an answer to.
    pub fn handle_line(&mut self, line: &str) -> Option<Value> {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            return None;
        }
        let parsed: Value = match serde_json::from_str(trimmed) {
            Ok(value) => value,
            Err(err) => {
                return Some(error_response(
                    Value::Null,
                    &RpcError::new(PARSE_ERROR, format!("invalid JSON: {err}")),
                ));
            }
        };
        self.handle_value(parsed)
    }

    /// A single request, or a batch of them.
    pub fn handle_value(&mut self, value: Value) -> Option<Value> {
        if let Value::Array(items) = value {
            // The spec is explicit: an empty array is not a batch, it is an
            // invalid request, and the answer is one error object, not [].
            if items.is_empty() {
                return Some(error_response(
                    Value::Null,
                    &RpcError::new(INVALID_REQUEST, "an empty batch is not a request"),
                ));
            }
            let mut responses = Vec::new();
            for item in items {
                if let Some(response) = self.handle_one(item) {
                    responses.push(response);
                }
            }
            return if responses.is_empty() {
                None
            } else {
                Some(Value::Array(responses))
            };
        }
        self.handle_one(value)
    }

    fn handle_one(&mut self, value: Value) -> Option<Value> {
        let request: RawRequest = match serde_json::from_value(value) {
            Ok(request) => request,
            Err(_) => {
                return Some(error_response(
                    Value::Null,
                    &RpcError::new(INVALID_REQUEST, "expected an object with a method"),
                ));
            }
        };

        // Only a request that carries an `id` gets an answer. The id may be a
        // string or a number, and a notification that fails still gets silence.
        let id = request.id.clone();

        if request.jsonrpc.as_deref() != Some("2.0") {
            return Some(error_response(
                id.unwrap_or(Value::Null),
                &RpcError::new(INVALID_REQUEST, "jsonrpc must be \"2.0\""),
            ));
        }

        let Some(method) = request.method else {
            return Some(error_response(
                id.unwrap_or(Value::Null),
                &RpcError::new(INVALID_REQUEST, "missing method"),
            ));
        };

        self.handled += 1;
        let outcome = self.call(&method, request.params);

        let id = id?;
        Some(match outcome {
            Ok(result) => json!({ "jsonrpc": "2.0", "id": id, "result": result }),
            Err(error) => error_response(id, &error),
        })
    }

    fn call(&mut self, method: &str, params: Option<Value>) -> Result<Value, RpcError> {
        match method {
            "add" => {
                let params = params.unwrap_or(Value::Null);
                let a = integer(&params, "a")?;
                let b = integer(&params, "b")?;
                Ok(json!({ "sum": a + b }))
            }
            "echo" => Ok(params.unwrap_or(Value::Null)),
            "notes.put" => {
                let params = params.unwrap_or(Value::Null);
                let title = string(&params, "title")?;
                let body = string(&params, "body")?;
                self.notes.insert(title.to_owned(), body.to_owned());
                Ok(json!({ "stored": self.notes.len() }))
            }
            "notes.list" => {
                let notes: Vec<Value> = self
                    .notes
                    .iter()
                    .map(|(title, body)| json!({ "title": title, "body": body }))
                    .collect();
                Ok(json!({ "notes": notes, "count": notes.len() }))
            }
            "notes.drop" => {
                let params = params.unwrap_or(Value::Null);
                let title = string(&params, "title")?;
                Ok(json!({ "removed": self.notes.remove(title).is_some() }))
            }
            other => Err(RpcError::new(
                METHOD_NOT_FOUND,
                format!("unknown method: {other}"),
            )),
        }
    }
}

fn integer(params: &Value, field: &str) -> Result<i64, RpcError> {
    params.get(field).and_then(Value::as_i64).ok_or_else(|| {
        RpcError::with_data(
            INVALID_PARAMS,
            format!("params.{field} must be an integer"),
            params.clone(),
        )
    })
}

fn string<'a>(params: &'a Value, field: &str) -> Result<&'a str, RpcError> {
    params.get(field).and_then(Value::as_str).ok_or_else(|| {
        RpcError::with_data(
            INVALID_PARAMS,
            format!("params.{field} must be a string"),
            params.clone(),
        )
    })
}
