from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from {{ package_name }} import client as deep
from {{ package_name }} import spec as spec_module

API = "http://api.test"
NOTE = {"id": "1", "title": "first", "tags": ["a"], "pinned": False}


def transport_for(
    status: int, body: object, calls: list[dict[str, Any]] | None = None
) -> Callable[..., tuple[int, str]]:
    def send(
        method: str, url: str, headers: dict[str, str], payload: bytes | None
    ) -> tuple[int, str]:
        if calls is not None:
            calls.append({"method": method, "url": url, "headers": headers, "payload": payload})
        return status, body if isinstance(body, str) else json.dumps(body)

    return send


def test_a_conforming_response_keeps_its_status_and_body(spec) -> None:
    reply = deep.Client(spec, base_url=API, transport=transport_for(200, [NOTE])).call("listNotes")
    assert reply.status == 200
    assert reply.body == [NOTE]
    assert reply.problems == ()


def test_the_request_uses_the_method_and_url_the_document_describes(spec) -> None:
    calls: list[dict[str, Any]] = []
    deep.Client(spec, base_url=API, transport=transport_for(200, [NOTE], calls)).call(
        "listNotes", {"limit": 2}
    )
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == f"{API}/notes?limit=2"


def test_a_request_body_is_json_and_declared_as_such(spec) -> None:
    calls: list[dict[str, Any]] = []
    deep.Client(spec, base_url=API, transport=transport_for(201, NOTE, calls)).call(
        "createNote", body={"title": "x"}
    )
    assert calls[0]["method"] == "POST"
    assert calls[0]["headers"]["content-type"] == "application/json"
    assert json.loads(calls[0]["payload"]) == {"title": "x"}


def test_a_documented_error_status_is_a_normal_answer(spec) -> None:
    reply = deep.Client(
        spec, base_url=API, transport=transport_for(404, {"error": "not_found"})
    ).call("getNote", {"id": "9"})
    assert reply.status == 404
    assert reply.body == {"error": "not_found"}


def test_an_undocumented_status_is_drift(spec) -> None:
    client = deep.Client(spec, base_url=API, transport=transport_for(500, {}))
    with pytest.raises(deep.DriftError) as caught:
        client.call("listNotes")
    assert "does not describe" in str(caught.value)
    assert caught.value.problems == ("status 500: not one of 200, 422",)


def test_a_response_that_breaks_the_schema_names_every_member(spec) -> None:
    broken = {"id": "1", "title": "first", "tags": 7, "pinned": False, "server_side": True}
    client = deep.Client(spec, base_url=API, transport=transport_for(200, [broken]))
    with pytest.raises(deep.DriftError) as caught:
        client.call("listNotes")
    assert "$[0].tags: expected array, got integer" in caught.value.problems
    assert "$[0]: unexpected member 'server_side'" in caught.value.problems


def test_a_body_that_is_not_json_is_drift(spec) -> None:
    client = deep.Client(spec, base_url=API, transport=transport_for(200, "<html>"))
    with pytest.raises(deep.DriftError) as caught:
        client.call("listNotes")
    assert "not JSON" in caught.value.problems[0]


def test_an_empty_body_where_one_is_described_is_drift(spec) -> None:
    client = deep.Client(spec, base_url=API, transport=transport_for(200, ""))
    with pytest.raises(deep.DriftError) as caught:
        client.call("listNotes")
    assert caught.value.problems == ("$: the document describes a body but the response was empty",)


def test_an_invalid_request_never_reaches_the_transport(spec) -> None:
    calls: list[dict[str, Any]] = []
    client = deep.Client(spec, base_url=API, transport=transport_for(201, NOTE, calls))
    with pytest.raises(deep.DriftError) as caught:
        client.call("createNote", body={"title": ""})
    assert calls == []
    assert caught.value.problems == ("request.title: shorter than 1 characters",)


def test_a_body_for_an_operation_without_one_is_refused(spec) -> None:
    client = deep.Client(spec, base_url=API, transport=transport_for(200, [NOTE]))
    with pytest.raises(spec_module.SpecError, match="declares no request body"):
        client.call("listNotes", body={"title": "x"})


def test_a_missing_body_for_an_operation_that_needs_one_is_refused(spec) -> None:
    client = deep.Client(spec, base_url=API, transport=transport_for(201, NOTE))
    with pytest.raises(spec_module.SpecError, match="needs a request body"):
        client.call("createNote")


def test_a_transport_failure_is_not_drift(spec) -> None:
    def send(
        method: str, url: str, headers: dict[str, str], payload: bytes | None
    ) -> tuple[int, str]:
        raise deep.TransportError("cannot reach the server")

    with pytest.raises(deep.TransportError):
        deep.Client(spec, base_url=API, transport=send).call("listNotes")


def test_the_server_comes_from_the_document_when_it_is_not_given(spec) -> None:
    assert (
        deep.Client(spec, transport=transport_for(200, [NOTE])).base_url == "http://127.0.0.1:5473"
    )


def test_a_document_without_a_server_needs_one_on_the_command_line() -> None:
    document = {
        "openapi": "3.1.0",
        "paths": {"/x": {"get": {"operationId": "x", "responses": {"200": {}}}}},
    }
    serverless = spec_module.Spec(
        document=document, operations=spec_module.operations_of(document), base_url=""
    )
    with pytest.raises(spec_module.SpecError, match="pass --base-url"):
        deep.Client(serverless)


def test_a_default_response_covers_statuses_the_document_does_not_list() -> None:
    document = {
        "openapi": "3.1.0",
        "paths": {
            "/x": {
                "get": {
                    "operationId": "x",
                    "responses": {
                        "200": {},
                        "default": {
                            "content": {"application/json": {"schema": {"type": "object"}}}
                        },
                    },
                }
            }
        },
    }
    operation = spec_module.operations_of(document)["x"]
    assert deep.response_schema(operation, 503) == {"type": "object"}
    assert deep.response_schema(operation, 200) == {}
