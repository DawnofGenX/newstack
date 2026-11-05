//! Entry point: binds `$PORT` (default 5462) and serves the text-statistics
//! contract. `--selftest` runs the offline assertion suite instead.

use {{ package_name }}::contract::{percent_decode, query_text};
use {{ package_name }}::counts::count;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--selftest") {
        let n = selftest();
        println!("selftest: {n} checks passed");
        return;
    }
    let rt = tokio_runtime();
    match rt {
        Ok(()) => {}
        Err(e) => {
            eprintln!("server error: {e}");
            std::process::exit(1);
        }
    }
}

/// `PORT` overrides the bind port; anything that is not a number is a usage error
/// (exit 2) rather than a silent fallback to 5462.
fn addr() -> String {
    let raw = std::env::var("PORT").unwrap_or_else(|_| "5462".to_string());
    match raw.parse::<u16>() {
        Ok(port) => format!("127.0.0.1:{port}"),
        Err(_) => {
            eprintln!("PORT must be a number, got {raw:?}");
            std::process::exit(2);
        }
    }
}

fn tokio_runtime() -> std::io::Result<()> {
    actix_web::rt::System::new().block_on({{ package_name }}::run(&addr()))
}

/// Wire-shape guard: the exact strings routes.rs emits must be valid JSON
/// with the pinned member set (routes.rs builds them with format!/literals,
/// never json! — serde_json's Map is a BTreeMap and re-sorts keys).
fn routes_body_shape(s: &str) -> bool {
    match serde_json::from_str::<serde_json::Value>(s) {
        Ok(v) => v.is_object(),
        Err(_) => false,
    }
}

/// Returns the number of assertions executed. Panics on the first failure.
pub fn selftest() -> u32 {
    let mut n = 0u32;
    macro_rules! ck {
        ($cond:expr) => {{
            n += 1;
            assert!(
                $cond,
                "selftest assertion {} failed: {}",
                n,
                stringify!($cond)
            );
        }};
    }

    // --- counting rules (contract fixtures first) ---
    let c = count("a b\n");
    ck!(c.lines == 1 && c.words == 2 && c.bytes == 4);
    let c = count("héllo wörld\n");
    ck!(c.lines == 1 && c.words == 2 && c.bytes == 14);
    let c = count("a b\nc\n");
    ck!(c.lines == 2 && c.words == 3 && c.bytes == 6);
    let c = count("");
    ck!(c.lines == 0 && c.words == 0 && c.bytes == 0);

    // delimiters: space, tab, LF, CR, VT, FF all split words
    ck!(count("a\tb").words == 2);
    ck!(count("a\r\nb").words == 2);
    ck!(count("a\x0bb").words == 2);
    ck!(count("a\x0cb").words == 2);
    ck!(count("   ").words == 0);
    ck!(count("\n\n\n").lines == 3 && count("\n\n\n").words == 0);
    ck!(count("one").words == 1 && count("one").lines == 0);
    ck!(count("a  b").words == 2); // double space: no phantom word
    ck!(count("a ").words == 1); // trailing space: no phantom word
                                 // bytes count the UTF-8 encoding, not chars
    ck!(count("é").bytes == 2);
    ck!(count("日本").bytes == 6);
    ck!(count("héllo").lines == 0);

    // --- percent decoding ---
    ck!(percent_decode("%C3%A9") == Some("é".into()));
    ck!(percent_decode("a+b") == Some("a b".into()));
    ck!(percent_decode("a%20b") == Some("a b".into()));
    ck!(percent_decode("%zz").is_none());
    ck!(percent_decode("%C").is_none()); // truncated escape
    ck!(percent_decode("plain") == Some("plain".into()));
    ck!(percent_decode("%c3%a9") == Some("é".into())); // lowercase hex

    // --- query_text extraction ---
    ck!(query_text("text=a+b") == Some(Some("a b".into())));
    ck!(query_text("other=1") == Some(None));
    ck!(query_text("") == Some(None));
    ck!(query_text("x=1&text=%C3%A9") == Some(Some("é".into())));
    ck!(query_text("text=%ZZ").is_none()); // malformed -> invalid_json path

    // --- JSON reply shape: key order + escaping (serde field order) ---
    let reply = {{ package_name }}::contract::StatsReply {
        text: "a\"b\nc".into(),
        lines: 1,
        words: 2,
        bytes: 6,
    };
    let j = serde_json::to_string(&reply).unwrap();
    ck!(j == "{\"text\":\"a\\\"b\\nc\",\"lines\":1,\"words\":2,\"bytes\":6}");
    ck!(j.starts_with("{\"text\":"));
    ck!(j.contains("\"lines\":1,\"words\":2,\"bytes\":6"));

    // wire error bodies are exact fixed strings (see routes.rs — never json!,
    // whose BTreeMap map ordering would sort detail before error on the 404)
    ck!(routes_body_shape(r#"{"status":"ok"}"#));
    ck!(routes_body_shape("{\"error\":\"method_not_allowed\"}"));
    ck!(routes_body_shape("{\"error\":\"missing_text\"}"));
    ck!(routes_body_shape("{\"error\":\"invalid_json\"}"));
    ck!(routes_body_shape(
        "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}"
    ));

    // POST body discrimination: missing vs wrong-type text
    let v: serde_json::Value = serde_json::from_str("{\"other\":1}").unwrap();
    ck!(v.as_object().unwrap().get("text").is_none());
    let v: serde_json::Value = serde_json::from_str("{\"text\":42}").unwrap();
    ck!(v.get("text").and_then(|t| t.as_str()).is_none());
    let bad: Result<serde_json::Value, _> = serde_json::from_str("{oops");
    ck!(bad.is_err());

    n
}
