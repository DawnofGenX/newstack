//! Wire contract: reply shapes, error bodies, and the query-string decoder.

use serde::Serialize;

/// Stats reply. Field order IS the JSON key order (serde preserves it):
/// text, lines, words, bytes.
#[derive(Debug, Serialize)]
pub struct StatsReply {
    pub text: String,
    pub lines: u64,
    pub words: u64,
    pub bytes: u64,
}

/// Percent-decode one `application/x-www-form-urlencoded`-style value:
/// `%XX` hex pairs (case-insensitive hex) decoded as raw bytes, `+` -> space.
/// Byte-level decode then lossy-UTF-8 so multi-byte sequences (e.g. `%C3%A9`
/// -> `é`) survive. Returns None on a malformed escape.
pub fn percent_decode(input: &str) -> Option<String> {
    let raw = input.as_bytes();
    let mut out: Vec<u8> = Vec::with_capacity(raw.len());
    let mut i = 0;
    while i < raw.len() {
        match raw[i] {
            b'%' => {
                if i + 3 > raw.len() {
                    return None; // truncated escape: need two hex digits
                }
                let hi = (raw[i + 1] as char).to_digit(16)?;
                let lo = (raw[i + 2] as char).to_digit(16)?;
                out.push((hi * 16 + lo) as u8);
                i += 3;
            }
            b'+' => {
                out.push(0x20);
                i += 1;
            }
            b => {
                out.push(b);
                i += 1;
            }
        }
    }
    Some(String::from_utf8_lossy(&out).into_owned())
}

/// Pure request->reply decision: no actix types anywhere in this module.
/// `Reply` is status + JSON body; routes.rs just wraps it into HttpResponse.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Reply {
    pub status: u16,
    pub body: String,
}

impl Reply {
    fn err(status: u16, body: &str) -> Reply {
        Reply {
            status,
            body: body.to_string(),
        }
    }
    fn stats(text: String) -> Reply {
        let c = crate::counts::count(&text);
        let body = serde_json::to_string(&StatsReply {
            text,
            lines: c.lines,
            words: c.words,
            bytes: c.bytes,
        })
        .unwrap();
        Reply { status: 200, body }
    }
}

/// Resolve (method, path, raw query, optional body) to the contract reply.
/// path must not include the query string.
pub fn dispatch(method: &str, path: &str, query: &str, body: Option<&[u8]>) -> Reply {
    match path {
        "/health" => {
            if method == "GET" {
                Reply {
                    status: 200,
                    body: "{\"status\":\"ok\"}".into(),
                }
            } else {
                Reply::err(405, "{\"error\":\"method_not_allowed\"}")
            }
        }
        "/stats" => match method {
            "GET" => match query_text(query) {
                Some(Some(text)) => Reply::stats(text),
                Some(None) => Reply::err(422, "{\"error\":\"missing_text\"}"),
                None => Reply::err(422, "{\"error\":\"invalid_json\"}"),
            },
            "POST" => {
                let value: Result<serde_json::Value, _> =
                    serde_json::from_slice(body.unwrap_or(b""));
                match value {
                    Err(_) => Reply::err(422, "{\"error\":\"invalid_json\"}"),
                    Ok(v) => match v.as_object().and_then(|o| o.get("text")) {
                        None if v.as_object().is_some() => {
                            Reply::err(422, "{\"error\":\"missing_text\"}")
                        }
                        Some(serde_json::Value::String(s)) => Reply::stats(s.clone()),
                        Some(_) => Reply::err(422, "{\"error\":\"invalid_json\"}"),
                        None => Reply::err(422, "{\"error\":\"invalid_json\"}"),
                    },
                }
            }
            _ => Reply::err(405, "{\"error\":\"method_not_allowed\"}"),
        },
        _ => Reply {
            status: 404,
            body: format!(
                "{{\"error\":\"not_found\",\"detail\":\"no route for {method} {path}\"}}"
            ),
        },
    }
}

/// Pull the `text=` parameter out of a raw query string (no leading `?`).
/// Returns: Some(Some(decoded)) when present, Some(None) when the query is
/// well-formed but has no `text` member, None when a component fails to decode.
pub fn query_text(raw_query: &str) -> Option<Option<String>> {
    for pair in raw_query.split('&') {
        if pair.is_empty() {
            continue;
        }
        let (k, v) = match pair.split_once('=') {
            Some(kv) => kv,
            None => (pair, ""),
        };
        let key = percent_decode(k)?;
        if key == "text" {
            return Some(Some(percent_decode(v)?));
        }
    }
    Some(None)
}
