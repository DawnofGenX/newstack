"""A client whose every response is checked against the document it was built from.

The point is not to be clever about HTTP. It is to make a server that has drifted
from its spec fail at the call site, with the exact member and the exact reason,
instead of quietly returning a value the caller will misread.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .schema import validate
from .spec import Operation, Spec, SpecError, build_url


class TransportError(RuntimeError):
    """The request never produced a response."""


class DriftError(ValueError):
    """The server answered, but not the way the document says it does."""

    def __init__(self, message: str, problems: list[str] | None = None) -> None:
        super().__init__(message)
        self.problems = tuple(problems or ())


@dataclass(frozen=True)
class Reply:
    operation_id: str
    method: str
    url: str
    status: int
    body: object
    problems: tuple[str, ...] = field(default=())

    def ok(self) -> bool:
        return not self.problems


Transport = Callable[[str, str, dict[str, str], bytes | None], tuple[int, str]]


def urllib_transport(timeout: float = 10.0) -> Transport:
    """The default transport: urllib, with 4xx/5xx bodies kept.

    An error status is a response like any other — the document may well describe
    its body — so an HTTPError is unpacked rather than raised.
    """

    def send(
        method: str,
        url: str,
        headers: dict[str, str],
        payload: bytes | None,
    ) -> tuple[int, str]:
        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return int(response.status), response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            with error:
                return int(error.code), error.read().decode("utf-8", "replace")
        except urllib.error.URLError as error:
            raise TransportError(f"cannot reach {url}: {error.reason}") from error
        except TimeoutError as error:
            raise TransportError(f"{url} did not answer within {timeout:g}s") from error

    return send


def response_schema(operation: Operation, status: int) -> dict[str, Any] | None:
    """The schema the document attaches to this status, or to `default`."""
    family = f"{status // 100}XX"
    for key in (str(status), family, "default"):
        if key in operation.responses:
            return operation.responses[key]
    return None


def _body_problems(operation: Operation, spec: Spec, body: object) -> list[str]:
    if operation.request_schema is None:
        if body is not None:
            raise SpecError(f"{operation.operation_id} declares no request body")
        return []
    if body is None:
        raise SpecError(f"{operation.operation_id} needs a request body")
    problems = validate(body, operation.request_schema, spec.document, "$")
    return [f"request{problem[1:]}" for problem in problems]


class Client:
    def __init__(
        self,
        spec: Spec,
        base_url: str | None = None,
        transport: Transport | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.spec = spec
        self.base_url = (base_url or spec.base_url).rstrip("/")
        if not self.base_url:
            raise SpecError("the document declares no server; pass --base-url")
        self.transport = transport or urllib_transport(timeout)

    def url_of(self, operation_id: str, params: dict[str, object] | None = None) -> str:
        operation = self.spec.operation(operation_id)
        return build_url(self.base_url, operation, dict(params or {}))

    def call(
        self,
        operation_id: str,
        params: dict[str, object] | None = None,
        body: object = None,
    ) -> Reply:
        operation = self.spec.operation(operation_id)
        problems = _body_problems(operation, self.spec, body)
        if problems:
            raise DriftError(f"{operation_id}: the request does not fit the document", problems)

        url = build_url(self.base_url, operation, dict(params or {}))
        headers = {"accept": "application/json"}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["content-type"] = "application/json"

        status, text = self.transport(operation.method, url, headers, payload)
        return self.check(operation, url, status, text)

    def check(self, operation: Operation, url: str, status: int, text: str) -> Reply:
        """Validate one already-received response. Shared with `validate --response`."""
        declared = response_schema(operation, status)
        if declared is None:
            known = ", ".join(sorted(operation.responses)) or "none"
            message = (
                f"{operation.operation_id}: the server answered {status}, "
                "which the document does not describe"
            )
            raise DriftError(message, [f"status {status}: not one of {known}"])

        problems: list[str] = []
        parsed: object = None
        if text.strip():
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as error:
                problems.append(f"$: the body is not JSON ({error.msg} at line {error.lineno})")
        elif declared:
            problems.append("$: the document describes a body but the response was empty")

        if not problems and declared:
            problems = validate(parsed, declared, self.spec.document, "$")

        reply = Reply(
            operation_id=operation.operation_id,
            method=operation.method,
            url=url,
            status=status,
            body=parsed,
            problems=tuple(problems),
        )
        if problems:
            raise DriftError(
                f"{operation.operation_id}: the response does not fit the document",
                problems,
            )
        return reply
