"""The resource side: a token is only a fence if somebody compares it."""

from __future__ import annotations

from dataclasses import dataclass, field


class StaleToken(RuntimeError):
    """A write arrived from a holder that has already been replaced."""

    def __init__(self, token: int, last_seen: int) -> None:
        super().__init__(
            f"token {token} is older than the last write (token {last_seen}): "
            "this holder's lease expired and somebody else owns the resource now"
        )
        self.token = token
        self.last_seen = last_seen


@dataclass
class FencedValue:
    """A value that remembers which token last wrote it."""

    value: str = ""
    token: int = 0
    writes: int = 0
    history: list[tuple[int, str]] = field(default_factory=list)

    def write(self, token: int, value: str) -> None:
        if token < self.token:
            raise StaleToken(token, self.token)
        # The same token may write many times inside one lease; only a NEWER lease takes
        # the resource away, which is what makes the compare monotonic rather than a lock.
        if token > self.token:
            self.token = token
        self.value = value
        self.writes += 1
        self.history.append((token, value))


@dataclass
class UnfencedValue:
    """The same resource with the fence removed: last writer wins, including the ghost."""

    value: str = ""
    writes: int = 0
    history: list[tuple[int, str]] = field(default_factory=list)

    def write(self, token: int, value: str) -> None:
        self.value = value
        self.writes += 1
        self.history.append((token, value))


def attempt(value: FencedValue | UnfencedValue, token: int, text: str) -> str:
    """Write if the fence allows it; report what happened either way."""
    try:
        value.write(token, text)
    except StaleToken as error:
        return f"refused: {error}"
    return f"accepted: {text!r} at token {token}"
