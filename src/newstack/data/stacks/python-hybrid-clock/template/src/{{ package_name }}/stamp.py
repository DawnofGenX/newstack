"""The timestamp itself: physical time, a logical counter, and who said it."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering


class StampError(ValueError):
    """A stamp that cannot be compared honestly."""


@total_ordering
@dataclass(frozen=True)
class Stamp:
    """One point in the hybrid order.

    ``physical_ms`` is the highest wall time the sender had seen when the event
    happened, ``logical`` breaks ties inside one millisecond, and ``node`` breaks
    the remaining ties so the order is total on every machine.

    Comparing stamps without the node makes two events in the same microsecond
    "equal", which silently loses the user's ordering, so the node is part of the
    key and the comparison never returns zero for two different nodes.
    """

    physical_ms: int
    logical: int = 0
    node: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.physical_ms, bool) or not isinstance(self.physical_ms, int):
            raise StampError(f"physical_ms must be a whole number, not {self.physical_ms!r}")
        if self.physical_ms < 0:
            raise StampError(f"physical_ms cannot be negative, not {self.physical_ms}")
        if isinstance(self.logical, bool) or not isinstance(self.logical, int):
            raise StampError(f"logical must be a whole number, not {self.logical!r}")
        if self.logical < 0:
            raise StampError(f"logical cannot be negative, not {self.logical}")
        if "|" in self.node or "@" in self.node:
            raise StampError(f"a node name cannot contain '|' or '@': {self.node!r}")

    def key(self) -> tuple[int, int, str]:
        """The sort key, spelled out so callers cannot invent a different one."""
        return (self.physical_ms, self.logical, self.node)

    def text(self) -> str:
        """``000000001700000000000:0000003@node-a`` — sortable as a string too."""
        return f"{self.physical_ms:018d}:{self.logical:07d}@{self.node}"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Stamp):
            return NotImplemented
        return self.key() < other.key()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Stamp):
            return NotImplemented
        return self.key() == other.key()

    def __hash__(self) -> int:
        return hash(self.key())


_PATTERN = re.compile(r"^([0-9]{1,19}):([0-9]{1,9})@(\S+)$")


def parse_stamp(text: str) -> Stamp:
    """Read back what :meth:`Stamp.text` wrote, refusing anything else."""
    match = _PATTERN.match(text.strip())
    if match is None:
        raise StampError(
            f"{text!r} is not a stamp; the shape is <physical_ms>:<logical>@<node>"
        )
    return Stamp(int(match.group(1)), int(match.group(2)), match.group(3))
