//! Integration entry: the same suite the `--selftest` binary mode runs.
//! Counting, percent-decoding, JSON escaping, routing-table shapes.

use {{ package_name }}::contract::{percent_decode, query_text, StatsReply};
use {{ package_name }}::counts::count;

#[test]
fn contract_fixtures() {
    let c = count("a b\n");
    assert_eq!((c.lines, c.words, c.bytes), (1, 2, 4));
    let c = count("héllo wörld\n");
    assert_eq!((c.lines, c.words, c.bytes), (1, 2, 14));
    let c = count("a b\nc\n");
    assert_eq!((c.lines, c.words, c.bytes), (2, 3, 6));
    let c = count("");
    assert_eq!((c.lines, c.words, c.bytes), (0, 0, 0));
}

#[test]
fn delimiter_matrix() {
    for d in [b' ', b'\t', b'\n', b'\r', 0x0Bu8, 0x0Cu8] {
        let s = format!("a{}b", d as char);
        assert_eq!(count(&s).words, 2, "delimiter {d:#04x} must split words");
    }
    assert_eq!(count("a\x0bb").lines, 0); // VT is not a line terminator
}

#[test]
fn utf8_byte_counting() {
    assert_eq!(count("é").bytes, 2);
    assert_eq!(count("héllo wörld").bytes, 13); // 11 chars, 13 bytes
}

#[test]
fn percent_decoding() {
    assert_eq!(percent_decode("%C3%A9").as_deref(), Some("é"));
    assert_eq!(percent_decode("%c3%a9").as_deref(), Some("é"));
    assert_eq!(percent_decode("a+b").as_deref(), Some("a b"));
    assert_eq!(percent_decode("a%20b").as_deref(), Some("a b"));
    assert!(percent_decode("%zz").is_none());
    assert!(percent_decode("%C").is_none());
}

#[test]
fn query_extraction() {
    assert_eq!(query_text("text=%C3%A9"), Some(Some("é".into())));
    assert_eq!(query_text("text=a+b"), Some(Some("a b".into())));
    assert_eq!(query_text("other=1"), Some(None));
    assert_eq!(query_text(""), Some(None));
    assert!(query_text("text=%ZZ").is_none());
}

#[test]
fn stats_reply_json_key_order_and_escaping() {
    let j = serde_json::to_string(&StatsReply {
        text: "a\"b\nc".into(),
        lines: 1,
        words: 2,
        bytes: 6,
    })
    .unwrap();
    assert_eq!(
        j,
        "{\"text\":\"a\\\"b\\nc\",\"lines\":1,\"words\":2,\"bytes\":6}"
    );
}

#[test]
fn routing_table_error_bodies() {
    assert_eq!(
        serde_json::json!({"status":"ok"}).to_string(),
        "{\"status\":\"ok\"}"
    );
    assert!(
        serde_json::json!({"error":"not_found","detail":"no route for GET /x"})
            .to_string()
            .contains("no route for GET /x")
    );
    assert_eq!(
        serde_json::json!({"error":"method_not_allowed"}).to_string(),
        "{\"error\":\"method_not_allowed\"}"
    );
}

#[test]
fn post_body_discrimination() {
    let v: serde_json::Value = serde_json::from_str("{\"other\":1}").unwrap();
    assert!(v.as_object().unwrap().get("text").is_none()); // -> missing_text
    let v: serde_json::Value = serde_json::from_str("{\"text\":42}").unwrap();
    assert!(v.get("text").unwrap().as_str().is_none()); // -> invalid_json
    assert!(serde_json::from_str::<serde_json::Value>("{oops").is_err()); // -> invalid_json
}
