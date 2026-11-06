"""Six stories about what a signature actually covers.

Each story is computed, so a regression turns it into a failure rather than a
stale paragraph in a README.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from .canonical import request_line
from .sign import Verifier, sign

SECRET = "demo-secret-do-not-reuse"
NOW = 1_780_000_000


@dataclass(frozen=True)
class Story:
    title: str
    lines: tuple[str, ...]
    held: bool


def _raw(secret: str, text: str) -> str:
    return hmac.new(secret.encode(), text.encode(), hashlib.sha256).hexdigest()


def reordering_story() -> Story:
    url = "/items?b=2&a=1"
    reordered = "/items?a=1&b=2"
    signature = sign(SECRET, "GET", url, timestamp=NOW)
    verifier = Verifier(SECRET)
    verdict = verifier.verify("GET", reordered, signature, now_s=NOW)
    naive_signed = _raw(SECRET, "GET " + url)
    naive_checked = _raw(SECRET, "GET " + reordered)
    lines = (
        f"signed url      {url}",
        f"sent url        {reordered}",
        f"canonical       {request_line('GET', url)[1]} and {request_line('GET', reordered)[1]}",
        f"verdict         {verdict.line()}",
        "a signature over the raw url would compare "
        f"{naive_signed[:12]}… with {naive_checked[:12]}…",
        "and those differ, which is why the naive version fails on a copy",
    )
    return Story("1. reordering the query does not invalidate the signature", lines,
                 verdict.ok and naive_signed != naive_checked)


def spelling_story() -> Story:
    escaped, plain = "/files/%7Euser/report", "/files/~user/report"
    plus = request_line("GET", "/search?q=a+b")[1]
    space = request_line("GET", "/search?q=a%20b")[1]
    signature = sign(SECRET, "GET", escaped, timestamp=NOW)
    verdict = Verifier(SECRET).verify("GET", plain, signature, now_s=NOW)
    lines = (
        f"escaped path    {escaped}",
        f"plain path      {plain}",
        f"canonical       {request_line('GET', plain)[1]}",
        f"verdict         {verdict.line()}",
        f"a plus sign     {plus}",
        f"a space         {space}",
        "they are different characters, and form encoding writes a space as a plus",
    )
    return Story("2. two spellings of one path agree, two characters do not", lines,
                 verdict.ok and plus != space and "%2B" in plus and "%20" in space)


def body_story() -> Story:
    signature = sign(SECRET, "POST", "/transfers", timestamp=NOW, body=b'{"amount": 10}')
    verifier = Verifier(SECRET)
    tampered = verifier.verify("POST", "/transfers", signature, now_s=NOW,
                               body=b'{"amount": 1000000}')
    intact = Verifier(SECRET).verify("POST", "/transfers", signature, now_s=NOW,
                                     body=b'{"amount": 10}')
    lines = (
        f"body signed     {b'{\"amount\": 10}'!r}",
        f"intact          {intact.line()}",
        f"tampered        {tampered.line()}",
        "the body hash is part of the signing string, so the amount is covered",
    )
    return Story("3. the body is covered, byte for byte", lines,
                 intact.ok and not tampered.ok)


def expiry_story() -> Story:
    signature = sign(SECRET, "GET", "/report", timestamp=NOW, ttl_s=300)
    at_the_edge = Verifier(SECRET).verify("GET", "/report", signature, now_s=NOW + 300)
    late = Verifier(SECRET).verify("GET", "/report", signature, now_s=NOW + 301)
    lines = (
        f"issued          {signature.timestamp} ({signature.expires - signature.timestamp} s)",
        f"expires         {signature.expires}",
        f"exactly on time {at_the_edge.line()}",
        f"one second late {late.line()}",
        "expiry is an integer comparison, not a guess about latency",
    )
    return Story("4. expiry is arithmetic", lines,
                 at_the_edge.ok and not late.ok and late.reason.endswith("1 s ago"))


def header_story() -> Story:
    headers = {"x-user": "alice", "content-type": "application/json"}
    loose = sign(SECRET, "POST", "/orders", timestamp=NOW, headers=headers,
                 signed_headers=("x-user",))
    changed = {**headers, "content-type": "text/plain"}
    loose_verdict = Verifier(SECRET).verify("POST", "/orders", loose, now_s=NOW,
                                            headers=changed)
    tight = sign(SECRET, "POST", "/orders", timestamp=NOW, headers=headers,
                 signed_headers=("x-user", "content-type"))
    tight_verdict = Verifier(SECRET).verify("POST", "/orders", tight, now_s=NOW,
                                            headers=changed)
    lines = (
        "signed headers  x-user only",
        "content-type    changed from application/json to text/plain",
        f"x-user only     {loose_verdict.line()}",
        f"both signed     {tight_verdict.line()}",
        "a header outside the signed set was never covered: sign what you trust",
    )
    return Story("5. a header you did not sign can be changed", lines,
                 loose_verdict.ok and not tight_verdict.ok)


def replay_story() -> Story:
    signature = sign(SECRET, "POST", "/orders", timestamp=NOW, ttl_s=300)
    verifier = Verifier(SECRET)
    first = verifier.verify("POST", "/orders", signature, now_s=NOW)
    second = verifier.verify("POST", "/orders", signature, now_s=NOW + 2)
    forgotten = verifier.forget_expired(NOW + 400)
    after = verifier.verify("POST", "/orders", signature,
                            now_s=signature.expires + 1)
    lines = (
        f"first use       {first.line()}",
        f"second use      {second.line()}",
        f"forget_expired  dropped {forgotten} nonce(s) once they can no longer be replayed",
        f"after expiry    {after.line()}",
        "a signature is a one-time token inside its lifetime, and a dead one afterwards",
    )
    return Story("6. the same signature cannot be used twice", lines,
                 first.ok and not second.ok and "already accepted" in second.reason
                 and not after.ok)


def stories() -> list[Story]:
    return [
        reordering_story(),
        spelling_story(),
        body_story(),
        expiry_story(),
        header_story(),
        replay_story(),
    ]


def render_stories() -> str:
    blocks = []
    for story in stories():
        blocks.append(story.title)
        blocks.extend(f"  {line}" for line in story.lines)
        blocks.append("  -> holds" if story.held else "  -> BROKEN")
        blocks.append("")
    return "\n".join(blocks) + "\n"
