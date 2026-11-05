"""Check the checker.

A validator that is silently wrong is worse than no validator, so this exercises the
schema rules, the URL builder, and two live servers: one that obeys the document and
one that has drifted from it.
"""

from __future__ import annotations

import importlib.util
import threading
from collections.abc import Callable
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .client import Client, DriftError
from .schema import type_name, validate
from .spec import Spec, SpecError, build_url, coerce, load

SPEC_PATH = Path("fixtures/openapi.json")
SERVER_PATH = Path("fixtures/server.py")


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []

    def ok(self, label: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            print(f"ok     {label}")
        else:
            self.failed.append(label)
            print(f"FAIL   {label}{': ' + detail if detail else ''}")

    def equal(self, label: str, actual: object, expected: object) -> None:
        self.ok(label, actual == expected, f"expected {expected!r}, got {actual!r}")

    def raises(
        self,
        label: str,
        error: type[Exception],
        call: Callable[[], object],
        contains: str = "",
    ) -> None:
        try:
            call()
        except error as caught:
            text = str(caught) + " " + " ".join(getattr(caught, "problems", ()))
            self.ok(label, contains in text, f"{contains!r} is not in {text!r}")
        except Exception as caught:
            self.ok(label, False, f"raised {type(caught).__name__}: {caught}")
        else:
            self.ok(label, False, "nothing was raised")


def _load_server_module() -> Any:
    specification = importlib.util.spec_from_file_location("_notes_server", SERVER_PATH)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot import {SERVER_PATH}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _start(drift: bool) -> tuple[ThreadingHTTPServer, int]:
    handler = _load_server_module().make_handler(drift)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.02},
        daemon=True,
    )
    thread.start()
    return server, int(server.server_address[1])


VALID_NOTE: dict[str, Any] = {
    "id": "1",
    "title": "first",
    "tags": ["a", "b"],
    "pinned": False,
    "body": None,
    "priority": "normal",
}


def _schema_checks(checks: Checks, spec: Spec) -> None:
    document = spec.document
    note = {"$ref": "#/components/schemas/Note"}
    checks.equal("true is a boolean, not an integer", type_name(True), "boolean")
    checks.equal("1 is an integer", type_name(1), "integer")
    checks.equal("1.5 is a number", type_name(1.5), "number")
    checks.equal("a valid note has no problems", validate(VALID_NOTE, note, document), [])

    bad_tags = validate({**VALID_NOTE, "tags": 7}, note, document)
    checks.ok(
        "a number where an array belongs is named with its path",
        bad_tags == ["$.tags: expected array, got integer"],
        repr(bad_tags),
    )

    extra = validate({**VALID_NOTE, "server_side": True}, note, document)
    checks.ok("an undeclared member is reported", "$: unexpected member 'server_side'" in extra)

    missing = validate({"id": "1", "tags": [], "pinned": True}, note, document)
    checks.ok(
        "a missing required member is reported", "$: missing required member 'title'" in missing
    )

    enum = validate({**VALID_NOTE, "priority": "urgent"}, note, document)
    checks.ok("an enum value out of range is reported", any("is not one of" in p for p in enum))

    checks.ok(
        "a boolean does not satisfy an integer",
        validate(True, {"type": "integer"}, document) == ["$: expected integer, got boolean"],
    )
    checks.ok(
        "a null body is allowed by type [string, null]",
        validate({**VALID_NOTE, "body": None}, note, document) == [],
    )
    checks.ok(
        "an object where a string belongs is reported",
        validate({"error": {"nested": True}}, {"$ref": "#/components/schemas/Error"}, document)
        == ["$.error: expected string, got object"],
    )


def _spec_checks(checks: Checks, spec: Spec) -> None:
    checks.equal(
        "three operations are declared",
        sorted(spec.operations),
        ["createNote", "getNote", "listNotes"],
    )
    checks.equal("the server comes from the document", spec.base_url, "http://127.0.0.1:5473")
    checks.equal(
        "the path parameter is required",
        spec.operation("getNote").required_parameters(),
        ("id",),
    )
    checks.raises(
        "an unknown operation is refused",
        SpecError,
        lambda: spec.operation("deleteNote"),
        "deleteNote",
    )

    operation = spec.operation("getNote")
    base = "http://127.0.0.1:5473"
    checks.equal(
        "path values are percent-encoded",
        build_url(base, operation, {"id": "a/b"}),
        "http://127.0.0.1:5473/notes/a%2Fb",
    )
    checks.equal(
        "query values are encoded",
        build_url(base, spec.operation("listNotes"), {"limit": 2}),
        "http://127.0.0.1:5473/notes?limit=2",
    )
    checks.raises(
        "an undeclared parameter is refused",
        SpecError,
        lambda: build_url(base, operation, {"nope": 1}),
        "nope",
    )
    checks.raises(
        "a missing path parameter is refused",
        SpecError,
        lambda: build_url(base, operation, {}),
        "id",
    )
    checks.equal(
        "text becomes the integer the schema declares", coerce("7", {"type": "integer"}), 7
    )
    checks.equal("yes is true", coerce("yes", {"type": "boolean"}), True)
    checks.raises(
        "bad text for an integer is refused",
        SpecError,
        lambda: coerce("seven", {"type": "integer"}),
    )


def _live_checks(checks: Checks, spec: Spec) -> None:
    honest, honest_port = _start(drift=False)
    drifted, drifted_port = _start(drift=True)
    try:
        client = Client(spec, base_url=f"http://127.0.0.1:{honest_port}")
        reply = client.call("listNotes")
        checks.ok(
            "a conforming response is accepted",
            isinstance(reply.body, list) and len(reply.body) == 2,
        )
        checks.equal("the status is kept", reply.status, 200)

        created = client.call("createNote", body={"title": "third", "tags": ["x"]})
        checks.equal("a documented 201 is accepted", created.status, 201)
        checks.equal("the created note carries the title", created.body["title"], "third")

        fetched = client.call("getNote", params={"id": "2"})
        checks.equal("an optional member may be absent", fetched.body["id"], "2")

        checks.raises(
            "a request that breaks the document never leaves the process",
            DriftError,
            lambda: client.call("createNote", body={"title": ""}),
            "shorter than 1 characters",
        )
        checks.raises(
            "a server that answers 500 to a documented 200 is drift",
            DriftError,
            lambda: Client(
                spec,
                base_url="http://127.0.0.1:1",
                transport=lambda *arguments: (500, "{}"),
            ).call("listNotes"),
            "does not describe",
        )

        broken = Client(spec, base_url=f"http://127.0.0.1:{drifted_port}")
        try:
            broken.call("listNotes")
        except DriftError as error:
            checks.ok(
                "three kinds of drift are all reported",
                len(error.problems) >= 3,
                repr(error.problems),
            )
        else:
            checks.ok("three kinds of drift are all reported", False, "no drift was detected")
    finally:
        honest.shutdown()
        drifted.shutdown()
        honest.server_close()
        drifted.server_close()


def run_selftest() -> bool:
    checks = Checks()
    spec = load(SPEC_PATH)
    _schema_checks(checks, spec)
    _spec_checks(checks, spec)
    _live_checks(checks, spec)
    total = checks.passed + len(checks.failed)
    if checks.failed:
        print(f"selftest: {len(checks.failed)} of {total} checks failed")
        return False
    print(f"selftest: {checks.passed} checks passed")
    return True
