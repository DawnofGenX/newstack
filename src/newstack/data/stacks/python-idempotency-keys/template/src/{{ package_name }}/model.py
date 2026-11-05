"""The vocabulary of an idempotent request: a key, a fingerprint, an outcome."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

VERSION = 1
KEY = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
STATES = ("claimed", "completed")


class InputError(ValueError):
    """Something the caller has to fix."""


class Mismatch(InputError):
    """The key already names a different request."""

    def __init__(self, key: str, first: str, second: str) -> None:
        self.key = key
        self.first = first
        self.second = second
        super().__init__(
            f"key {key} was first used for a different request ({first} != {second}); "
            "a key names one intent, and reusing it for another is a bug in the caller"
        )


class InProgress(RuntimeError):
    """Another worker holds the key right now."""

    def __init__(self, key: str, retry_after_s: float) -> None:
        self.key = key
        self.retry_after_s = retry_after_s
        super().__init__(
            f"key {key} is in flight in another worker; retry in {retry_after_s:.3f}s "
            "rather than charging the card again"
        )


class OwnerLost(RuntimeError):
    """This worker no longer holds the key."""

    def __init__(self, key: str, attempt: int) -> None:
        self.key = key
        self.attempt = attempt
        super().__init__(
            f"key {key} is no longer held by attempt {attempt}; the lease expired and "
            "another worker took it over, so this result must not be stored"
        )


def canonical(body: Mapping[str, Any]) -> str:
    """The bytes the fingerprint is taken over: key order and spacing cancelled."""
    try:
        return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except TypeError as error:
        raise InputError(f"body is not JSON-serialisable: {error}") from error


@dataclass(frozen=True)
class Request:
    """One intended effect, named by a client-supplied key."""

    scope: str
    key: str
    body: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.scope, str) or not self.scope.strip():
            raise InputError(f"scope must be a non-empty string, got {self.scope!r}")
        if not isinstance(self.key, str) or not KEY.match(self.key):
            raise InputError(
                f"key {self.key!r} must be 8-128 characters of A-Z, a-z, 0-9, '_' or '-'; "
                "a key short enough to guess is a key two clients will share"
            )
        if not isinstance(self.body, Mapping):
            raise InputError(f"body must be a mapping, got {type(self.body).__name__}")

    @property
    def fingerprint(self) -> str:
        return fingerprint_of(self.scope, self.body)


def fingerprint_of(scope: str, body: Mapping[str, Any]) -> str:
    material = canonical({"scope": scope, "body": body})
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Response:
    """What the handler decided, stored verbatim so a replay is byte-identical."""

    status: int
    body: str

    def __post_init__(self) -> None:
        if isinstance(self.status, bool) or not isinstance(self.status, int):
            raise InputError(f"status must be an integer, got {self.status!r}")
        if not 100 <= self.status <= 599:
            raise InputError(f"status {self.status} is not an HTTP status code")
        if not isinstance(self.body, str):
            raise InputError(f"body must be text, got {type(self.body).__name__}")


@dataclass(frozen=True)
class Outcome:
    """The answer a caller gets, whether it ran or was replayed."""

    key: str
    status: int
    body: str
    replay: bool
    attempts: int

    @property
    def executed(self) -> bool:
        return not self.replay

    def line(self) -> str:
        verdict = "replay" if self.replay else "execute"
        return f"{verdict:<8} {self.key:<20} status {self.status} attempts {self.attempts}"
