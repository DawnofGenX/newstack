"""The sketch: rows of cells, the min of rows, the audit after every add.

A count-min sketch seats counts in ``depth`` rows of ``width``
cells; a key lands on one cell per row and its answer is the min of
those cells. The promise this package makes, and checks after every
single update, is that the min of rows never dips under the truth —
the sketch drifts up (a shared cell reads high), never under. With
the shipped configuration the rows are bijections on the universe,
so on the shipped corpora the min equals the truth exactly; that
equality is a property of the width, not of the idea, and the edges
say so. Determinism is total: same seed, same answers.
"""

from __future__ import annotations

from .hashes import DEPTH, MULTIPLIERS, WIDTH, cell_of
from .keys import ensure_key


class SketchError(ValueError):
    """The sketch was asked for a shape it cannot hold."""


def _valid_shape(width: int, depth: int, multipliers: tuple[int, ...]) -> None:
    if width <= 0 or depth <= 0:
        raise SketchError(f"no sketch from {width}x{depth}")
    if len(multipliers) < depth:
        raise SketchError(f"{depth} rows need {depth} multipliers")
    for multiplier in multipliers[:depth]:
        if multiplier <= 0 or multiplier % 2 == 0:
            raise SketchError(f"row multiplier {multiplier} is not odd and positive")


class CountMinSketch:
    """A fixed-grid counter whose answer is the min across its rows."""

    def __init__(
        self,
        width: int = WIDTH,
        depth: int = DEPTH,
        multipliers: tuple[int, ...] = MULTIPLIERS,
    ) -> None:
        _valid_shape(width, depth, multipliers)
        self.width = width
        self.depth = depth
        self.multipliers = tuple(multipliers[:depth])
        self.rows: list[list[int]] = [[0] * width for _ in range(depth)]
        self._truth: dict[int, int] = {}

    def _cells(self, key: int) -> list[int]:
        return [cell_of(key, row, self.multipliers, self.width) for row in range(self.depth)]

    def add(self, key: int, n: int = 1) -> None:
        """Seat n more for key, then audit every tracked count."""
        key = ensure_key(key)
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            raise SketchError(f"no increment of {n!r}: updates are positive ints")
        self._truth[key] = self._truth.get(key, 0) + n
        for row in range(self.depth):
            self.rows[row][self._cells(key)[row]] += n
        broken = self.audit()
        if broken:
            raise SketchError(f"audit caught {broken[0]}")

    def count(self, key: int) -> int:
        """The min of the rows the key visits; never under the truth."""
        key = ensure_key(key)
        cells = self._cells(key)
        return min(self.rows[row][cells[row]] for row in range(self.depth))

    def audit(self) -> list[str]:
        """Every tracked key whose answer dips under its ledger truth."""
        broken: list[str] = []
        for key, truth in sorted(self._truth.items()):
            if self.count(key) < truth:
                broken.append(f"count({key}) undercounts {self.count(key)} < {truth}")
        return broken

    def true_count(self, key: int) -> int:
        """The ledger answer: exactly what was added for key."""
        return self._truth.get(ensure_key(key), 0)

    def keys(self) -> list[int]:
        """The tracked keys, in ascending order."""
        return sorted(self._truth)

    def __contains__(self, key: object) -> bool:
        """Whether the ledger tracks this key at all."""
        return key in self._truth

    def __iter__(self):
        """Tracked keys, ascending — the ledger's reading order."""
        return iter(sorted(self._truth))

    def __len__(self) -> int:
        """The number of keys the ledger tracks."""
        return len(self._truth)

    @property
    def total(self) -> int:
        """Everything the ledger has ever been fed."""
        return sum(self._truth.values())

    @property
    def updates(self) -> int:
        """The number of keys the ledger tracks."""
        return len(self._truth)

    def report(self) -> dict[str, object]:
        """The shape as a caller would print it."""
        return {
            "width": self.width,
            "depth": self.depth,
            "multipliers": list(self.multipliers),
            "tracked": len(self._truth),
            "total": self.total,
        }

    def cells_of(self, key: int) -> list[int]:
        """The cells a key visits, one per row — the audit's map."""
        return self._cells(ensure_key(key))
