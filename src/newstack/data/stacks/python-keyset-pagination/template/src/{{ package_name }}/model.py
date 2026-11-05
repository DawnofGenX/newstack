"""The vocabulary: an order, a query, a cursor, a page.

The cursor is the interesting object. It names a POSITION in one result set —
the sort key and the id of the last row you saw — so the next page is "the rows
after this one", never "the next twenty rows". That is the difference between
keyset and offset, and it is why the cursor has to remember the query it was
made for.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field

KEYS = ("created_at", "title")
DIRECTIONS = ("asc", "desc")
CURSOR_VERSION = 1


class InputError(ValueError):
    """Something the caller can fix: a bad order, a forged cursor, a bad size."""


@dataclass(frozen=True)
class Order:
    """A total order: the sort key plus the primary key, because a sort key alone ties."""

    key: str = "created_at"
    descending: bool = False

    def __post_init__(self) -> None:
        if self.key not in KEYS:
            raise InputError(f"unknown sort key {self.key!r}; expected one of {', '.join(KEYS)}")

    @property
    def arrow(self) -> str:
        return "desc" if self.descending else "asc"

    def line(self) -> str:
        return f"{self.key} {self.arrow}, id {self.arrow}"

    def columns(self) -> str:
        direction = "DESC" if self.descending else "ASC"
        return f"{self.key} {direction}, id {direction}"

    def comparison(self) -> str:
        """The row-value comparison that advances one page, in portable SQL."""
        operator = "<" if self.descending else ">"
        key, ident = self.key, "id"
        return f"({key}, {ident}) {operator} (?, ?)"


@dataclass(frozen=True)
class Query:
    """A filtered, ordered result set. The fingerprint is what a cursor is bound to."""

    order: Order = field(default_factory=Order)
    title_prefix: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.title_prefix, str):
            raise InputError("title_prefix must be a string")

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.order.key,
            "descending": self.order.descending,
            "title_prefix": self.title_prefix,
        }

    def canonical(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()[:12]


@dataclass(frozen=True)
class Cursor:
    """Where the last page ended: the sort value, the id, and the query it belongs to."""

    sort_value: object
    ident: int
    fingerprint: str
    version: int = CURSOR_VERSION

    def as_dict(self) -> dict[str, object]:
        return {
            "v": self.version,
            "sort": self.sort_value,
            "id": self.ident,
            "query": self.fingerprint,
        }

    def encode(self) -> str:
        """Opaque to the client: base64url JSON without padding."""
        blob = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))
        return base64.urlsafe_b64encode(blob.encode()).decode().rstrip("=")

    @classmethod
    def decode(cls, text: str) -> Cursor:
        if not isinstance(text, str) or not text.strip():
            raise InputError("cursor must be a non-empty string")
        padded = text + "=" * (-len(text) % 4)
        try:
            blob = base64.urlsafe_b64decode(padded.encode())
        except (ValueError, TypeError) as error:
            raise InputError(f"cursor is not base64url: {error}") from None
        try:
            payload = json.loads(blob)
        except json.JSONDecodeError as error:
            raise InputError(f"cursor is not JSON: {error}") from None
        if not isinstance(payload, dict):
            raise InputError("cursor is not an object")
        for member in ("sort", "id", "query"):
            if member not in payload:
                raise InputError(f"cursor is missing {member!r}")
        version = payload.get("v", CURSOR_VERSION)
        if version != CURSOR_VERSION:
            raise InputError(
                f"cursor version {version!r} is not supported (this build is {CURSOR_VERSION})"
            )
        ident = payload["id"]
        if isinstance(ident, bool) or not isinstance(ident, int):
            raise InputError(f"cursor id must be an integer, got {ident!r}")
        fingerprint = payload["query"]
        if not isinstance(fingerprint, str) or not fingerprint:
            raise InputError(f"cursor query must be a fingerprint string, got {fingerprint!r}")
        return cls(payload["sort"], ident, fingerprint, version)

    def check(self, query: Query) -> None:
        if self.fingerprint != query.fingerprint:
            raise InputError(
                f"cursor was made for a different query ({self.fingerprint} != "
                f"{query.fingerprint}); a cursor names a position in one result set, "
                "not in any"
            )


@dataclass(frozen=True)
class Page:
    rows: tuple[dict[str, object], ...]
    next_cursor: str | None
    prev_cursor: str | None
    fingerprint: str

    @property
    def size(self) -> int:
        return len(self.rows)

    @property
    def ids(self) -> list[int]:
        return [int(row["id"]) for row in self.rows]

    def as_dict(self) -> dict[str, object]:
        return {
            "rows": list(self.rows),
            "next_cursor": self.next_cursor,
            "prev_cursor": self.prev_cursor,
            "query": self.fingerprint,
            "size": self.size,
        }
