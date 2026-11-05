"""The same rules through Litestar's router, on a real ASGI scope, no socket."""

from __future__ import annotations

import pytest
from litestar.testing import TestClient

from {{ package_name }}.app import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert (response.status_code, response.text) == (200, '{"status":"ok"}')
    assert response.headers["content-type"] == "application/json"


def test_stats_query(client: TestClient) -> None:
    response = client.get("/stats", params={"text": "a b\n"})
    assert response.status_code == 200
    assert response.json() == {"text": "a b\n", "lines": 1, "words": 2, "bytes": 4}


def test_the_query_string_is_not_read_twice(client: TestClient) -> None:
    """Litestar's `raw_path` carries `?query`; adding `query_string` again doubles it."""
    response = client.get("/stats?text=a+b")
    assert response.json() == {"text": "a b", "lines": 1, "words": 2, "bytes": 3}


def test_percent_encoded_utf8_reaches_the_counter_as_bytes(client: TestClient) -> None:
    response = client.get("/stats?text=h%C3%A9llo")
    assert response.json() == {"text": "héllo", "lines": 1, "words": 1, "bytes": 6}


def test_missing_text(client: TestClient) -> None:
    assert client.get("/stats").json() == {"error": "missing_text"}


def test_a_bad_percent_escape_is_missing_not_an_error_page(client: TestClient) -> None:
    assert client.get("/stats?text=%zz").json() == {"error": "missing_text"}


def test_stats_post(client: TestClient) -> None:
    response = client.post("/stats", json={"text": "a b\n"})
    assert response.status_code == 200
    assert response.json()["bytes"] == 4


def test_post_without_a_text_member(client: TestClient) -> None:
    response = client.post("/stats", content='{"text":1}')
    assert (response.status_code, response.text) == (422, '{"error":"missing_text"}')


def test_post_with_a_broken_body(client: TestClient) -> None:
    response = client.post("/stats", content="not json")
    assert (response.status_code, response.text) == (422, '{"error":"invalid_json"}')


def test_wrong_method_on_a_known_path(client: TestClient) -> None:
    response = client.put("/health")
    assert (response.status_code, response.json()) == (405, {"error": "method_not_allowed"})


def test_head_reaches_the_contract_rather_than_litestar(client: TestClient) -> None:
    """Litestar answers HEAD for a GET route itself; the catch-all claims it first."""
    response = client.head("/health")
    assert response.status_code == 405


def test_unknown_route_echoes_the_raw_target(client: TestClient) -> None:
    response = client.get("/nope?x=1")
    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "detail": "no route for GET /nope?x=1"}


def test_the_root_is_a_404_not_a_missing_route(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 404
    assert response.json()["detail"] == "no route for GET /"


def test_the_reply_key_order_is_fixed(client: TestClient) -> None:
    body = client.get("/stats?text=a").text
    assert body == '{"text":"a","lines":1,"words":1,"bytes":1}'


def test_a_body_is_not_required_for_get(client: TestClient) -> None:
    assert client.request("GET", "/stats?text=x", content=b"ignored").status_code == 200
