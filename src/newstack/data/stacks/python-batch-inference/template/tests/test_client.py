"""Retries are proven against a real socket, not asserted."""

from __future__ import annotations

import pytest

from {{ package_name }}.client import ChatClient, RequestFailed

from .stub import serve


@pytest.fixture
def stub():
    server, state = serve(flaky_after=2)
    yield f"http://127.0.0.1:{server.server_address[1]}/v1", state
    server.shutdown()
    server.server_close()


def test_answers_and_reports_usage(stub) -> None:
    base_url, _state = stub
    output, tokens_in, tokens_out, attempts = ChatClient(base_url).complete("hi there")
    assert output == "echo: hi there"
    assert (tokens_in, tokens_out, attempts) == (2, 1, 1)


def test_retries_a_429_with_growing_backoff_and_succeeds(stub) -> None:
    base_url, state = stub
    delays: list[float] = []
    client = ChatClient(base_url, backoff=0.05, max_attempts=4, sleep=delays.append)
    output, _tokens_in, _tokens_out, attempts = client.complete("FAIL429 please")
    assert output == "echo: FAIL429 please"
    assert attempts == 3
    assert delays == [0.05, 0.1]
    assert state.attempts["FAIL429 please"] == 3


def test_a_400_fails_on_the_first_attempt_without_sleeping(stub) -> None:
    base_url, _state = stub
    delays: list[float] = []
    client = ChatClient(base_url, sleep=delays.append)
    with pytest.raises(RequestFailed, match="http 400"):
        client.complete("FAIL400 nope")
    assert delays == []


def test_gives_up_after_max_attempts_and_says_so(stub) -> None:
    base_url, _state = stub
    client = ChatClient(base_url, max_attempts=2, backoff=0.0, sleep=lambda _s: None)
    with pytest.raises(RequestFailed, match=r"gave up after 2 attempts \(http 429"):
        client.complete("FAIL429 forever")


def test_an_unreachable_endpoint_is_a_network_failure() -> None:
    client = ChatClient("http://127.0.0.1:9/v1", max_attempts=2, backoff=0.0, sleep=lambda _s: None)
    with pytest.raises(RequestFailed, match="gave up after 2 attempts"):
        client.complete("anything")


def test_the_payload_shape_is_asserted_without_a_socket() -> None:
    import json

    payload = json.loads(ChatClient("http://x/v1", model="m").payload("hi"))
    assert payload == {"model": "m", "messages": [{"role": "user", "content": "hi"}]}
