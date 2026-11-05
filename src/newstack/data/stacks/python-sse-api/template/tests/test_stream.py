"""Tests: unit tests for the format and a real socket test that proves streaming."""

from __future__ import annotations

import json
import socket
import threading
import time
from collections.abc import Iterator

import pytest
import uvicorn
from fastapi.testclient import TestClient

from {{ package_name }}.counts import count_text
from {{ package_name }}.main import create_app
from {{ package_name }}.wire import encode_event, parse_events


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


def test_count_text_matches_wc() -> None:
    assert count_text("hello world\n") == count_text("hello world\n")
    counts = count_text("hello world\n")
    assert (counts.lines, counts.words, counts.bytes) == (1, 2, 12)
    assert count_text("héllo wörld\n").bytes == 14, "two accents add two bytes"


def test_a_newline_inside_data_is_split_into_repeated_fields() -> None:
    raw = encode_event("one\ntwo", event="note", event_id="7")
    assert raw == "id: 7\nevent: note\ndata: one\ndata: two\n\n"
    assert parse_events(raw) == [{"id": "7", "event": "note", "data": "one\ntwo"}]


def test_comments_are_not_events() -> None:
    assert parse_events(": keep-alive\n\n") == []


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_the_stream_names_its_content_type(client: TestClient) -> None:
    with client.stream("GET", "/stream?count=2&delay=0") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers["cache-control"].startswith("no-cache")
        body = "".join(response.iter_text())
    events = parse_events(body)
    assert [event["event"] for event in events] == ["tick", "tick", "done"]
    assert [event["id"] for event in events if event["event"] == "tick"] == ["1", "2"]
    assert json.loads(events[-1]["data"]) == {"ticks": 2, "resumed_from": 0}


def test_a_resume_continues_instead_of_replaying(client: TestClient) -> None:
    with client.stream(
        "GET", "/stream?count=4&delay=0", headers={"Last-Event-ID": "2"}
    ) as response:
        body = "".join(response.iter_text())
    ticks = [event for event in parse_events(body) if event["event"] == "tick"]
    assert [event["id"] for event in ticks] == ["3", "4"]


def test_a_garbage_resume_header_falls_back_to_the_start(client: TestClient) -> None:
    with client.stream(
        "GET", "/stream?count=2&delay=0", headers={"Last-Event-ID": "not-a-number"}
    ) as response:
        body = "".join(response.iter_text())
    ticks = [event for event in parse_events(body) if event["event"] == "tick"]
    assert [event["id"] for event in ticks] == ["1", "2"]


def test_stats_stream_carries_running_totals(client: TestClient) -> None:
    with client.stream("GET", "/stats/stream?text=a%20b%0Ac&size=2&delay=0") as response:
        body = "".join(response.iter_text())
    events = parse_events(body)
    chunks = [event for event in events if event["event"] == "chunk"]
    assert len(chunks) == 3, "five characters in slices of two are three events"
    assert [json.loads(event["data"])["chunk"] for event in chunks] == ["a ", "b\n", "c"]
    first = json.loads(chunks[0]["data"])
    assert first["chunk"] == "a "
    assert first["words"] == 1
    last = json.loads(chunks[-1]["data"])
    assert (last["lines"], last["words"], last["bytes"]) == (1, 3, 5), "a, b and c are three words"
    assert json.loads(events[-1]["data"])["ticks"] == 3


def test_invalid_query_is_one_sentence(client: TestClient) -> None:
    response = client.get("/stream?count=0")
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_request"
    assert "count" in response.json()["detail"]


def test_unknown_route_keeps_its_detail(client: TestClient) -> None:
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "detail": "no route for GET /nope"}


def test_wrong_method_on_health_is_405(client: TestClient) -> None:
    response = client.post("/health")
    assert response.status_code == 405
    assert response.json()["error"] == "method_not_allowed"


def test_post_stream_without_json_is_422(client: TestClient) -> None:
    response = client.post("/stream", content=b"not json")
    assert response.status_code == 422
    assert response.json() == {"error": "invalid_json"}


def test_post_stream_with_json_is_405(client: TestClient) -> None:
    response = client.post("/stream", json={"count": 1})
    assert response.status_code == 405
    assert response.json()["detail"] == "POST /stream does not stream"


def _serve(app) -> tuple[uvicorn.Server, threading.Thread, int]:
    """Bind port 0: a fixed port makes the suite fail when anything else is listening."""
    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while time.time() < deadline:
        if server.started:
            port = server.servers[0].sockets[0].getsockname()[1]
            return server, thread, port
        time.sleep(0.05)
    raise AssertionError("uvicorn never started")


def test_events_arrive_one_by_one_over_a_real_socket() -> None:
    """The whole point: a client sees tick 1 before tick 3 exists.

    A response built as one string passes every other test in this file and still
    fails here, because the first read would only return after the last delay.
    """
    server, thread, port = _serve(create_app())
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=15) as sock:
            sock.sendall(b"GET /stream?count=3&delay=0.3 HTTP/1.1\r\nHost: x\r\n\r\n")
            sock.settimeout(15)

            # Read until the first event is complete: a loaded machine may take a
            # while to schedule the server, and that is not a streaming failure.
            first = b""
            deadline = time.time() + 15
            while b"data:" not in first or b"\n\n" not in first:
                assert time.time() < deadline, f"no first event within 15s: {first!r}"
                chunk = sock.recv(4096)
                if not chunk:
                    break
                first += chunk
            assert b"HTTP/1.1 200" in first
            assert b"event: tick" in first, first
            assert b'"seq":3' not in first, "the first read already held the whole stream"

            started = time.time()
            rest = b""
            while b"event: done" not in rest:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                rest += chunk
            elapsed = time.time() - started
        # Two more ticks at 0.3s each: the last two events cannot arrive together.
        assert elapsed >= 0.5, f"the remaining events did not wait for their delay ({elapsed:.2f}s)"
        assert b'"ticks":3' in rest
    finally:
        server.should_exit = True
        thread.join(timeout=10)
