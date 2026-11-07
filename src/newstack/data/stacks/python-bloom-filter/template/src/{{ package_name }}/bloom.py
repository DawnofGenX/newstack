"""The bit-array over ``[0, 256)``: add seats, might_contain asks.

One documented width, k deterministic rows per key. ``add`` raises
the key's rows; ``might_contain`` answers yes only when every row is
already raised. That asymmetry is the entire honest edge: a yes can
be another key's seating standing in for its own, so collisions may
only ever answer present — a no means some row of this key was
never raised by anything, and nothing can talk a raised bit back
down. Removal is not on the menu: clearing an item's rows erases
whatever else shares those bits, and a filter that says *no* to
what it was told is no filter at all.
"""

from __future__ import annotations

from .hashing import rows_for
from .universe import (
    UNIVERSE,
    UniverseError,
    ensure_key,
    ensure_seed,
)

WIDTH = 1024
ROWS = 4
SEED = 11
MIN_WIDTH = 8
MAX_WIDTH = 65_536
MAX_ROWS = 16


class BloomError(ValueError):
    """Raised when the array, its shape, or its file cannot be used."""


def _extent(value: object, low: int, high: int, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise BloomError(f"{what} {value!r} is not an integer")
    if not low <= value <= high:
        raise BloomError(f"{what} {value} leaves [{low}, {high}]")
    return value


def _width(value: object) -> int:
    return _extent(value, MIN_WIDTH, MAX_WIDTH, "width")


def _rows(value: object) -> int:
    return _extent(value, 1, MAX_ROWS, "rows")


class Bloom:
    """A fixed bit-array with k rows; the only promise is no false no."""

    def __init__(
        self,
        width: int = WIDTH,
        rows: int = ROWS,
        seed: int = SEED,
        bits: int = 0,
        added: tuple[int, ...] = (),
    ) -> None:
        self.width = _width(width)
        self.rows = _rows(rows)
        self.seed = ensure_seed(seed)
        if isinstance(bits, bool) or not isinstance(bits, int) or bits < 0:
            raise BloomError(f"bits {bits!r} is not a bit pattern")
        if bits >> self.width:
            raise BloomError(f"bits reach past the documented width {self.width}")
        self.bits = bits
        self.added: list[int] = [ensure_key(key) for key in added]

    def seats_of(self, key: int) -> tuple[int, ...]:
        """The documented seating: which rows raise for this key."""
        return rows_for(ensure_key(key), self.width, self.rows, self.seed)

    def add(self, key: int) -> int:
        """Raise the key's rows; return how many bits were freshly set."""
        key = ensure_key(key)
        fresh = 0
        for seat in self.seats_of(key):
            if not (self.bits >> seat) & 1:
                self.bits |= 1 << seat
                fresh += 1
        if key not in self.added:
            self.added.append(key)
        return fresh

    def might_contain(self, key: int) -> bool:
        """Yes when every row is raised; no only on a provably clear row."""
        key = ensure_key(key)
        return all((self.bits >> seat) & 1 for seat in self.seats_of(key))

    def first_clear_row(self, key: int) -> int | None:
        """Which row keeps an absent key honest (None: every row is set)."""
        for row, seat in enumerate(self.seats_of(key)):
            if not (self.bits >> seat) & 1:
                return row
        return None

    def audit(self) -> list[str]:
        """Every added key, re-asked: a broken filter names itself here."""
        return [
            f"key {key} reads absent after {len(self.added)} adds"
            for key in self.added
            if not self.might_contain(key)
        ]

    def survey(self) -> list[int]:
        """Absent keys that answer present: the honest edge, counted."""
        known = set(self.added)
        return [
            key
            for key in range(UNIVERSE)
            if key not in known and self.might_contain(key)
        ]

    @property
    def bits_set(self) -> int:
        return bin(self.bits).count("1")

    @property
    def fill(self) -> float:
        return self.bits_set / self.width

    def as_dict(self) -> dict[str, object]:
        return {
            "added": list(self.added),
            "bits": self.bits,
            "rows": self.rows,
            "seed": self.seed,
            "width": self.width,
        }

    @classmethod
    def from_dict(cls, payload: object) -> Bloom:
        if not isinstance(payload, dict):
            raise BloomError("a filter file is a JSON object")
        try:
            return cls(
                width=payload["width"],
                rows=payload["rows"],
                seed=payload["seed"],
                bits=payload["bits"],
                added=tuple(payload["added"]),
            )
        except KeyError as missing:
            raise BloomError(f"filter file has no {missing.args[0]!r}") from None
        except (TypeError, UniverseError) as broken:
            raise BloomError(f"filter file is unusable: {broken}") from None
