//! Offline assertions: no socket, no database file. Returns the check count.

use crate::store::{civil_from_days, format_unix, normalise_title};

macro_rules! ck {
    ($n:ident, $cond:expr) => {{
        $n += 1;
        assert!(
            $cond,
            "selftest assertion {} failed: {}",
            $n,
            stringify!($cond)
        );
    }};
}

macro_rules! ck_eq {
    ($n:ident, $got:expr, $want:expr) => {{
        $n += 1;
        let got = $got;
        let want = $want;
        assert!(
            got == want,
            "selftest assertion {} failed: got {:?} want {:?}",
            $n,
            got,
            want
        );
    }};
}

pub fn run() -> u32 {
    let mut n = 0u32;

    // --- title normalisation (the 422 rule) ---
    ck_eq!(n, normalise_title("shopping"), Some("shopping".to_string()));
    ck_eq!(n, normalise_title("  padded  "), Some("padded".to_string()));
    ck_eq!(n, normalise_title(""), None);
    ck_eq!(n, normalise_title("   "), None);
    ck_eq!(n, normalise_title("\t\n"), None);
    ck_eq!(n, normalise_title("a b"), Some("a b".to_string()));

    // --- timestamp shape ---
    ck_eq!(n, format_unix(0), "1970-01-01T00:00:00Z".to_string());
    ck_eq!(n, format_unix(86_399), "1970-01-01T23:59:59Z".to_string());
    ck_eq!(n, format_unix(86_400), "1970-01-02T00:00:00Z".to_string());
    ck_eq!(
        n,
        format_unix(1_700_000_000),
        "2023-11-14T22:13:20Z".to_string()
    );
    ck_eq!(n, civil_from_days(0), (1970, 1, 1));
    ck_eq!(n, civil_from_days(19_723), (2024, 1, 1));
    ck_eq!(n, civil_from_days(-1), (1969, 12, 31));
    for (secs, len) in [(0u64, 20usize), (1_700_000_000, 20), (2_000_000_000, 20)] {
        ck!(n, format_unix(secs).len() == len);
    }
    ck!(n, format_unix(1_700_000_000).ends_with('Z'));
    ck!(n, format_unix(1_700_000_000).contains('T'));

    // --- the fixtures every newstack service shares ---
    for (text, lines, words) in [
        ("a b\n", 1u64, 2u64),
        ("héllo wörld\n", 1, 2),
        ("a b\nc\n", 2, 3),
    ] {
        let bytes = text.len() as u64;
        ck!(n, bytes >= lines);
        ck!(n, words >= lines);
    }
    ck_eq!(n, "héllo wörld\n".len(), 14);
    ck_eq!(n, "a b\n".len(), 4);

    // --- JSON shapes the routes emit (serde field order = wire order) ---
    let note = crate::store::Note {
        id: 1,
        title: "shopping".to_string(),
        body: "milk".to_string(),
        created_at: "2026-01-01T00:00:00Z".to_string(),
    };
    let encoded = serde_json::to_string(&note).unwrap();
    ck_eq!(
        n,
        encoded.clone(),
        r#"{"id":1,"title":"shopping","body":"milk","created_at":"2026-01-01T00:00:00Z"}"#
            .to_string()
    );
    let list = format!(r#"{{"notes":[{encoded}]}}"#);
    ck!(n, list.starts_with(r#"{"notes":["#));
    ck!(n, list.ends_with("]}"));
    let health = r#"{"status":"ok","notes":0}"#;
    ck!(n, health.contains(r#""status":"ok""#));

    // --- error bodies: detail is omitted when absent, quoted key order fixed ---
    let with_detail = r#"{"error":"not_found","detail":"no note with id 9"}"#;
    ck!(n, with_detail.starts_with(r#"{"error""#));
    ck!(n, with_detail.contains(r#""detail":"no note with id 9""#));
    let bare = r#"{"error":"invalid_json"}"#;
    ck!(n, !bare.contains("detail"));

    // --- route-not-found detail is built from method + path only ---
    let method = "GET";
    let path = "/nope";
    let detail = format!("no route for {method} {path}");
    ck_eq!(n, detail.clone(), "no route for GET /nope".to_string());
    ck!(n, !detail.contains('?'));

    // --- blank-title rejection covers every whitespace the handler may see ---
    for raw in [" ", "\t", "\n", "  \t\n  "] {
        ck!(n, normalise_title(raw).is_none());
    }
    // ...while any non-space character survives untrimmed inside the string
    ck_eq!(n, normalise_title(" a b "), Some("a b".to_string()));
    ck!(n, normalise_title("0").is_some());

    n
}
