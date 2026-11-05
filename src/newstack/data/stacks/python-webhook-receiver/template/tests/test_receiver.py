"""End-to-end tests through TestClient: the signature rules, the ledger, and the wire."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from {{ package_name }} import signature
from {{ package_name }}.main import create_app

SECRET = "s3cr3t-value"
NOW = 1_700_000_000


def sign(body: bytes, timestamp: int = NOW, secret: str = SECRET) -> dict[str, str]:
    return {
        "X-Signature": signature.compute(secret, str(timestamp), body),
        "X-Timestamp": str(timestamp),
        "X-Event-Id": "evt-1",
        "Content-Type": "application/json",
    }


@pytest.fixture()
def client(tmp_path: Path):
    app = create_app(
        db_path=str(tmp_path / "events.db"),
        secrets={"github": SECRET},
        clock=lambda: NOW,
    )
    with TestClient(app) as active:
        yield active


def post(client, body: bytes, headers: dict[str, str] | None = None):
    return client.post("/webhooks/github", content=body, headers=headers or sign(body))


def test_health_starts_empty(client) -> None:
    answer = client.get("/health")
    assert answer.status_code == 200
    assert answer.json() == {"status": "ok", "events": 0}


def test_a_signed_event_is_accepted_once(client) -> None:
    body = b'{"kind": "push"}'
    first = post(client, body)
    assert first.status_code == 202
    assert first.json() == {
        "status": "accepted",
        "id": "evt-1",
        "source": "github",
        "kind": "push",
    }
    assert client.get("/health").json()["events"] == 1

    again = post(client, body)
    assert again.status_code == 200
    assert again.json()["status"] == "duplicate"
    assert client.get("/health").json()["events"] == 1, "a retry must not add a row"


def test_the_digest_is_over_the_bytes_that_arrived(client) -> None:
    """Whitespace that a JSON round trip would drop still changes the signature."""
    body = b'{"kind":"push",  "n": 1}'
    assert post(client, body).status_code == 202

    reserialised = json.dumps(json.loads(body)).encode()
    assert reserialised != body
    forged = dict(sign(body), **{"X-Event-Id": "evt-2"})
    forged["X-Signature"] = signature.compute(SECRET, str(NOW), reserialised)
    answer = post(client, body, forged)
    assert answer.status_code == 401
    assert answer.json() == {"error": "bad_signature"}


def test_a_wrong_secret_is_rejected(client) -> None:
    body = b'{"kind": "push"}'
    answer = post(client, body, sign(body, secret="not-the-secret"))
    assert answer.status_code == 401
    assert answer.json() == {"error": "bad_signature"}
    assert client.get("/health").json()["events"] == 0


def test_a_stale_timestamp_is_rejected(client) -> None:
    body = b'{"kind": "push"}'
    old = NOW - 3600
    answer = post(client, body, sign(body, timestamp=old))
    assert answer.status_code == 401
    assert answer.json() == {"error": "stale_timestamp"}


def test_missing_headers_are_rejected(client) -> None:
    body = b'{"kind": "push"}'
    answer = client.post("/webhooks/github", content=body, headers={"Content-Type": "text/plain"})
    assert answer.status_code == 401
    assert answer.json() == {"error": "missing_signature"}


def test_a_signed_body_that_is_not_json_is_a_422(client) -> None:
    body = b'{"kind": '
    answer = post(client, body)
    assert answer.status_code == 422
    assert answer.json()["error"] == "invalid_json"
    assert "detail" in answer.json()


def test_a_signed_event_without_an_id_is_a_400(client) -> None:
    body = b'{"kind": "push"}'
    headers = sign(body)
    del headers["X-Event-Id"]
    answer = post(client, body, headers)
    assert answer.status_code == 400
    assert answer.json() == {"error": "missing_event_id"}


def test_an_unknown_source_is_a_404(client) -> None:
    body = b'{"kind": "push"}'
    answer = client.post("/webhooks/gitlab", content=body, headers=sign(body))
    assert answer.status_code == 404
    assert answer.json()["error"] == "unknown_source"
    assert "s3cr3t" not in answer.text


def test_signature_helpers_are_pure() -> None:
    body = b"payload"
    digest = signature.compute(SECRET, "1700000000", body)
    assert digest.startswith("sha256=")
    assert len(digest) == len("sha256=") + 64
    assert digest == signature.compute(SECRET, "1700000000", body)
    assert signature.compute(SECRET, "1700000001", body) != digest
    assert signature.compute("other", "1700000000", body) != digest


def test_the_ledger_survives_a_new_connection(tmp_path: Path) -> None:
    path = str(tmp_path / "events.db")
    body = b'{"kind": "push"}'
    first = create_app(db_path=path, secrets={"github": SECRET}, clock=lambda: NOW)
    with TestClient(first) as client:
        assert post(client, body).status_code == 202
    second = create_app(db_path=path, secrets={"github": SECRET}, clock=lambda: NOW)
    with TestClient(second) as client:
        assert client.get("/health").json()["events"] == 1
        assert post(client, body).status_code == 200, "the duplicate check must survive a restart"


def test_events_are_listed_in_arrival_order(client) -> None:
    for index in (1, 2):
        body = json.dumps({"kind": "push", "n": index}).encode()
        headers = sign(body)
        headers["X-Event-Id"] = f"evt-{index}"
        assert post(client, body, headers).status_code == 202
    listed = client.get("/events").json()["events"]
    assert [row["id"] for row in listed] == ["evt-1", "evt-2"]


def test_route_and_method_errors_are_json(client) -> None:
    missing = client.get("/nope")
    assert missing.status_code == 404
    assert missing.json() == {"error": "not_found", "detail": "no route for GET /nope"}

    wrong = client.patch("/health")
    assert wrong.status_code == 405
    assert wrong.json() == {"error": "method_not_allowed"}


def test_a_timestamp_in_the_future_beyond_tolerance_is_stale(client) -> None:
    body = b'{"kind": "push"}'
    answer = post(client, body, sign(body, timestamp=NOW + 3600))
    assert answer.status_code == 401
    assert answer.json() == {"error": "stale_timestamp"}


def test_tolerance_boundary_is_inclusive() -> None:
    body = b"x"
    edge = NOW - signature.DEFAULT_TOLERANCE
    assert signature.verify(
        secret=SECRET,
        header=signature.compute(SECRET, str(edge), body),
        timestamp=str(edge),
        body=body,
        now=NOW,
    ) is None
    past = NOW - signature.DEFAULT_TOLERANCE - 1
    failure = signature.verify(
        secret=SECRET,
        header=signature.compute(SECRET, str(past), body),
        timestamp=str(past),
        body=body,
        now=NOW,
    )
    assert failure is not None and failure.kind == "stale_timestamp"


def test_now_is_only_read_from_the_injected_clock(client) -> None:
    """The app never calls time.time() for the replay window, so the tests stay stable."""
    body = b'{"kind": "push"}'
    assert abs(int(time.time()) - NOW) > 300, "the fixture clock must be far from real time"
    assert post(client, body).status_code == 202
