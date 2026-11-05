"""The contract, without Litestar in the picture at all."""

from __future__ import annotations

import pytest

from {{ package_name }} import counts
from {{ package_name }}.contract import percent_decode, quote, route


@pytest.mark.parametrize(
    ("target", "status", "body"),
    [
        ("/health", 200, '{"status":"ok"}'),
        ("/stats?text=a+b", 200, '{"text":"a b","lines":1,"words":2,"bytes":3}'),
        ("/stats?text=a%20b%0A", 200, '{"text":"a b\\u000a","lines":1,"words":2,"bytes":4}'),
        ("/stats?text=", 200, '{"text":"","lines":0,"words":0,"bytes":0}'),
        ("/stats", 422, '{"error":"missing_text"}'),
        ("/stats?text=%zz", 422, '{"error":"missing_text"}'),
        ("/stats?text=%4", 422, '{"error":"missing_text"}'),
        ("/stats?text=h%C3%A9llo", 200, '{"text":"héllo","lines":1,"words":1,"bytes":6}'),
        ("/nope", 404, '{"error":"not_found","detail":"no route for GET /nope"}'),
        ("/", 404, '{"error":"not_found","detail":"no route for GET /"}'),
        ("/nope?x=1", 404, '{"error":"not_found","detail":"no route for GET /nope?x=1"}'),
        ("/stats/extra", 404, '{"error":"not_found","detail":"no route for GET /stats/extra"}'),
    ],
)
def test_get_routes(target: str, status: int, body: str) -> None:
    assert route("GET", target) == (status, body)


@pytest.mark.parametrize(
    ("body", "status", "text"),
    [
        (b'{"text":"a b\\n"}', 200, '{"text":"a b\\u000a","lines":1,"words":2,"bytes":4}'),
        (b'{"text":""}', 200, '{"text":"","lines":0,"words":0,"bytes":0}'),
        (b'{"text":"h\\u00e9llo w\\u00f6rld\\n"}', 200,
         '{"text":"héllo wörld\\u000a","lines":1,"words":2,"bytes":14}'),
        (b'{"text":"\\ud83d\\ude00"}', 200, '{"text":"\U0001f600","lines":1,"words":1,"bytes":4}'),
        (b'{"text":1}', 422, '{"error":"missing_text"}'),
        (b'{"text":null}', 422, '{"error":"missing_text"}'),
        (b'{"nope":1}', 422, '{"error":"missing_text"}'),
        (b"[1,2]", 422, '{"error":"missing_text"}'),
        (b'"text"', 422, '{"error":"missing_text"}'),
        (b"", 422, '{"error":"missing_text"}'),
        (b"not json", 422, '{"error":"invalid_json"}'),
        (b'{"text":', 422, '{"error":"invalid_json"}'),
        (b'{"text":"a"} {"text":"b"}', 422, '{"error":"invalid_json"}'),
        (b"\xff\xfe", 422, '{"error":"invalid_json"}'),
    ],
)
def test_post_bodies(body: bytes, status: int, text: str) -> None:
    assert route("POST", "/stats", body) == (status, text)


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def test_health_only_answers_get(method: str) -> None:
    assert route(method, "/health") == (405, '{"error":"method_not_allowed"}')


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE", "HEAD"])
def test_stats_rejects_other_methods(method: str) -> None:
    assert route(method, "/stats") == (405, '{"error":"method_not_allowed"}')


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("", (0, 0, 0)),
        ("a", (1, 1, 1)),
        ("a b\n", (1, 2, 4)),
        ("a b", (1, 2, 3)),
        ("a\nb\n", (2, 2, 4)),
        ("a\n\nb", (3, 2, 4)),
        ("\t\r\n", (1, 0, 3)),
        ("héllo wörld\n", (1, 2, 14)),
        ("😀", (1, 1, 4)),
    ],
)
def test_wc_semantics(text: str, want: tuple[int, int, int]) -> None:
    data = text.encode("utf-8")
    assert (counts.lines(data), counts.words(data), counts.size(data)) == want


@pytest.mark.parametrize(
    ("raw", "want"),
    [("a+b", b"a b"), ("%41%42", b"AB"), ("%4", None), ("%", None), ("a b", b"a b"), ("%00", b"\x00")],
)
def test_percent_decode(raw: str, want: bytes | None) -> None:
    assert percent_decode(raw) == want


def test_the_first_text_parameter_wins() -> None:
    assert route("GET", "/stats?text=x&text=y")[1].startswith('{"text":"x"')


def test_quote_escapes_json_control_characters() -> None:
    assert quote('a"b\\c\n') == '"a\\"b\\\\c\\u000a"'


def test_the_reply_key_order_is_fixed() -> None:
    body = route("GET", "/stats?text=a")[1]
    assert body.index('"text"') < body.index('"lines"') < body.index('"words"') < body.index('"bytes"')
