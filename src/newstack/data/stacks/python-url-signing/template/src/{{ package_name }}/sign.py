"""Signing and verifying, with the refusals saying which rule failed.

The signing string is a list of lines, one fact per line, because a separator
that can appear inside a field is a separator that can be forged: a header value
containing a newline would otherwise move the boundary between facts.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from .canonical import CanonicalError, request_line

ALGORITHM = "hmac-sha256"
DEFAULT_TTL_S = 300
CLOCK_SKEW_S = 60


class SignatureError(ValueError):
    """The signature cannot be produced or read."""


def body_hash(body: bytes) -> str:
    """The hash of the body, and the hash of no body is still a hash."""
    return hashlib.sha256(body).hexdigest()


def _clean(value: str) -> str:
    """Collapse the whitespace a proxy may have rewritten."""
    return " ".join(value.split())


@dataclass(frozen=True)
class Signature:
    value: str
    timestamp: int
    expires: int
    signed_headers: tuple[str, ...]
    canonical: str
    algorithm: str = ALGORITHM
    target: str = ""

    def as_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "signature": self.value,
            "timestamp": self.timestamp,
            "expires": self.expires,
            "signed_headers": list(self.signed_headers),
        }

    @classmethod
    def from_dict(cls, payload: dict, canonical: str = "") -> Signature:
        try:
            return cls(
                value=str(payload["signature"]),
                timestamp=int(payload["timestamp"]),
                expires=int(payload["expires"]),
                signed_headers=tuple(str(name).lower() for name in payload.get(
                    "signed_headers", [])),
                canonical=canonical,
                algorithm=str(payload.get("algorithm", ALGORITHM)),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise SignatureError(f"this is not a signature: {error}") from error

    def lines(self) -> list[str]:
        lines = [
            f"algorithm    {self.algorithm}",
            f"timestamp    {self.timestamp}",
            f"expires      {self.expires} ({self.expires - self.timestamp} s of life)",
        ]
        if self.target:
            lines.append(f"target       {self.target}")
        lines.extend([
            f"headers      {', '.join(self.signed_headers) or '(none)'}",
            f"signature    {self.value}",
        ])
        return lines


def signing_string(
    method: str,
    url: str,
    *,
    timestamp: int,
    headers: dict[str, str] | None = None,
    body: bytes = b"",
    signed_headers: tuple[str, ...] = (),
) -> str:
    """The exact text the HMAC covers, one fact per line."""
    upper, target = request_line(method, url)
    given = {name.lower(): _clean(value) for name, value in (headers or {}).items()}
    lines = [ALGORITHM, str(timestamp), upper, target, body_hash(body)]
    for name in sorted(name.lower() for name in signed_headers):
        if name not in given:
            raise SignatureError(
                f"'{name}' is listed as signed but the request does not carry it, so the "
                "signature would cover a header nobody sent"
            )
        lines.append(f"{name}:{given[name]}")
    return "\n".join(lines)


def _digest(secret: str, text: str) -> str:
    return hmac.new(secret.encode("utf-8"), text.encode("utf-8"), hashlib.sha256).hexdigest()


def sign(
    secret: str,
    method: str,
    url: str,
    *,
    timestamp: int,
    headers: dict[str, str] | None = None,
    body: bytes = b"",
    signed_headers: tuple[str, ...] = (),
    ttl_s: int = DEFAULT_TTL_S,
) -> Signature:
    """Produce a signature for one request."""
    if ttl_s <= 0:
        raise SignatureError(f"a lifetime of {ttl_s} s would be useless: use a positive number")
    text = signing_string(
        method,
        url,
        timestamp=timestamp,
        headers=headers,
        body=body,
        signed_headers=signed_headers,
    )
    return Signature(
        value=_digest(secret, text),
        timestamp=timestamp,
        expires=timestamp + ttl_s,
        signed_headers=tuple(sorted(name.lower() for name in signed_headers)),
        canonical=text,
        target=text.split("\n")[3],
    )


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str

    def line(self) -> str:
        return f"{'ok' if self.ok else 'refused':<8} {self.reason}"


class Verifier:
    """Checks a signature and remembers which ones it has already accepted."""

    def __init__(
        self,
        secret: str,
        *,
        ttl_s: int = DEFAULT_TTL_S,
        skew_s: int = CLOCK_SKEW_S,
    ) -> None:
        if ttl_s <= 0:
            raise SignatureError("a verifier needs a positive signature lifetime")
        if skew_s < 0:
            raise SignatureError("a negative clock skew allowance would refuse the present")
        self.secret = secret
        self.ttl_s = ttl_s
        self.skew_s = skew_s
        self.seen: dict[str, int] = {}

    def verify(
        self,
        method: str,
        url: str,
        signature: Signature,
        *,
        now_s: int,
        headers: dict[str, str] | None = None,
        body: bytes = b"",
    ) -> Verdict:
        if signature.algorithm.lower() != ALGORITHM:
            return Verdict(False, f"algorithm '{signature.algorithm}' is not {ALGORITHM}")
        if signature.timestamp > now_s + self.skew_s:
            ahead = signature.timestamp - now_s
            return Verdict(
                False,
                f"issued {ahead} s in the future, past the {self.skew_s} s skew allowance",
            )
        if now_s > signature.expires:
            return Verdict(False, f"expired {now_s - signature.expires} s ago")
        try:
            text = signing_string(
                method,
                url,
                timestamp=signature.timestamp,
                headers=headers,
                body=body,
                signed_headers=signature.signed_headers,
            )
        except (SignatureError, CanonicalError) as error:
            return Verdict(False, f"this request cannot be canonicalised: {error}")
        expected = _digest(self.secret, text)
        if not hmac.compare_digest(expected, signature.value):
            return Verdict(False, "the signature does not match this request")
        used_at = self.seen.get(signature.value)
        if used_at is not None:
            return Verdict(False, f"this signature was already accepted at {used_at}")
        self.seen[signature.value] = now_s
        return Verdict(True, f"accepted, {signature.expires - now_s} s of life left")

    def forget_expired(self, now_s: int) -> int:
        """Drop nonces that can no longer be replayed."""
        stale = [value for value, used_at in self.seen.items()
                 if now_s - used_at > self.ttl_s + self.skew_s]
        for value in stale:
            del self.seen[value]
        return len(stale)
