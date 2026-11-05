"""Signature rules, kept away from the framework so they can be tested directly.

The digest is over the BYTES that arrived. Any layer that parses and re-serialises the
body changes those bytes (spacing, key order, unicode escapes), so verification has to
happen before anything else looks at the payload.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

PREFIX = "sha256="
DEFAULT_TOLERANCE = 300


@dataclass(frozen=True)
class Failure:
    """Why a signature did not verify. `kind` is what the HTTP layer maps to a status."""

    kind: str
    detail: str | None = None


def compute(secret: str, timestamp: str, body: bytes) -> str:
    """`sha256=<hex>` over `<timestamp>.<body>`, the shape most senders use."""
    mac = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("ascii") + body, hashlib.sha256)
    return PREFIX + mac.hexdigest()


def verify(
    *,
    secret: str,
    header: str | None,
    timestamp: str | None,
    body: bytes,
    now: int,
    tolerance: int = DEFAULT_TOLERANCE,
) -> Failure | None:
    """Return None when the signature is good, otherwise the reason it is not."""
    if not header:
        return Failure("missing_signature")
    if not timestamp:
        return Failure("missing_timestamp")
    try:
        arrived = int(timestamp)
    except ValueError:
        return Failure("bad_timestamp")
    if abs(now - arrived) > tolerance:
        return Failure("stale_timestamp")
    if not header.startswith(PREFIX):
        return Failure("bad_signature")
    expected = compute(secret, timestamp, body)
    # compare_digest, never `==`: a plain comparison leaks the prefix length through timing.
    if not hmac.compare_digest(expected, header):
        return Failure("bad_signature")
    return None
