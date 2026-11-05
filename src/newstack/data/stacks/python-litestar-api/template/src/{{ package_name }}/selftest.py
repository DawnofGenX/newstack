"""The contract checked without a socket: `python -m {{ package_name }} --selftest`.

Same assertions the tests make, in one file with no test framework, so a
generated project can be checked on a machine where nothing is installed but the
standard library and this package.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from .contract import percent_decode, quote, route

CASES: tuple[tuple[str, str, bytes, int, str], ...] = (
    # method, target, body, expected status, expected body
    ("GET", "/health", b"", 200, '{"status":"ok"}'),
    ("POST", "/health", b"", 405, '{"error":"method_not_allowed"}'),
    ("DELETE", "/health", b"", 405, '{"error":"method_not_allowed"}'),
    ("HEAD", "/health", b"", 405, '{"error":"method_not_allowed"}'),
    ("GET", "/stats?text=a+b", b"", 200, '{"text":"a b","lines":1,"words":2,"bytes":3}'),
    ("GET", "/stats?text=a%20b%0A", b"", 200, '{"text":"a b\\u000a","lines":1,"words":2,"bytes":4}'),
    ("GET", "/stats", b"", 422, '{"error":"missing_text"}'),
    ("GET", "/stats?text=", b"", 200, '{"text":"","lines":0,"words":0,"bytes":0}'),
    ("GET", "/stats?text=%zz", b"", 422, '{"error":"missing_text"}'),
    ("GET", "/stats?text=%", b"", 422, '{"error":"missing_text"}'),
    ("GET", "/stats?text=a%", b"", 422, '{"error":"missing_text"}'),
    ("POST", "/stats", b'{"text":"a b\\n"}', 200, '{"text":"a b\\u000a","lines":1,"words":2,"bytes":4}'),
    ("POST", "/stats", b'{"text":""}', 200, '{"text":"","lines":0,"words":0,"bytes":0}'),
    ("POST", "/stats", b'{"text":"h\\u00e9llo w\\u00f6rld\\n"}', 200,
     '{"text":"héllo wörld\\u000a","lines":1,"words":2,"bytes":14}'),
    ("POST", "/stats", b'{"text":"\\ud83d\\ude00"}', 200,
     '{"text":"\U0001f600","lines":1,"words":1,"bytes":4}'),
    ("POST", "/stats", b'{"text":1}', 422, '{"error":"missing_text"}'),
    ("POST", "/stats", b'{"nope":1}', 422, '{"error":"missing_text"}'),
    ("POST", "/stats", b"[1,2]", 422, '{"error":"missing_text"}'),
    ("POST", "/stats", b'"text"', 422, '{"error":"missing_text"}'),
    ("POST", "/stats", b"", 422, '{"error":"missing_text"}'),
    ("POST", "/stats", b"  ", 422, '{"error":"missing_text"}'),
    ("POST", "/stats", b"not json", 422, '{"error":"invalid_json"}'),
    ("POST", "/stats", b'{"text":', 422, '{"error":"invalid_json"}'),
    ("POST", "/stats", b'{"text":"a"} {"text":"b"}', 422, '{"error":"invalid_json"}'),
    ("POST", "/stats", b"\xff\xfe", 422, '{"error":"invalid_json"}'),
    ("PUT", "/stats", b"", 405, '{"error":"method_not_allowed"}'),
    ("PATCH", "/stats", b'{"text":"x"}', 405, '{"error":"method_not_allowed"}'),
    ("GET", "/nope", b"", 404, '{"error":"not_found","detail":"no route for GET /nope"}'),
    ("GET", "/", b"", 404, '{"error":"not_found","detail":"no route for GET /"}'),
    ("GET", "/stats/extra", b"", 404,
     '{"error":"not_found","detail":"no route for GET /stats/extra"}'),
    ("GET", "/nope?x=1", b"", 404,
     '{"error":"not_found","detail":"no route for GET /nope?x=1"}'),
)

COUNT_CASES: tuple[tuple[str, int, int, int], ...] = (
    ("", 0, 0, 0),
    ("a", 1, 1, 1),
    ("a b\n", 1, 2, 4),
    ("a b", 1, 2, 3),
    ("a\nb\n", 2, 2, 4),
    ("a\n\nb", 3, 2, 4),
    ("  padded  ", 1, 1, 10),
    ("\t\r\n", 1, 0, 3),
    ("héllo wörld\n", 1, 2, 14),
    ("😀", 1, 1, 4),
)


def check(condition: bool, label: str, detail: str = "") -> int:
    if condition:
        return 1
    print(f"FAIL {label}{': ' + detail if detail else ''}", flush=True)
    return 0


def run() -> int:
    failures = 0
    total = 0

    for method, target, body, status, expected in CASES:
        total += 1
        got_status, got_body = route(method, target, body)
        failures += not check(
            (got_status, got_body) == (status, expected),
            f"{method} {target}",
            f"want {status} {expected!r}, got {got_status} {got_body!r}",
        )

    for text, want_lines, want_words, want_bytes in COUNT_CASES:
        total += 1
        status, body = route("GET", "/stats?text=" + quote_plus(text), b"")
        tail = f'"lines":{want_lines},"words":{want_words},"bytes":{want_bytes}}}'
        failures += not check(
            status == 200 and body.endswith(tail), f"count {text!r}", f"got {status} {body!r}"
        )

    total += 4
    failures += not check(percent_decode("a+b") == b"a b", "decode plus")
    failures += not check(percent_decode("%41%42") == b"AB", "decode hex")
    failures += not check(percent_decode("%4") is None, "decode short escape")
    failures += not check(quote('a"b\\c') == '"a\\"b\\\\c"', "quote escapes")

    total += 1
    failures += not check(
        route("GET", "/stats?text=x&text=y", b"")[1].startswith('{"text":"x"'),
        "first text param wins",
    )

    total += 1
    failures += not check(
        route("GET", "/stats?text=a%00b", b"")[0] == 200, "escaped NUL is text, not a terminator"
    )

    print(f"selftest: {total - failures}/{total} checks passed", flush=True)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
