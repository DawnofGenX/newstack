"""Banding: turning a signature into a candidate set, with an S-curve you can print.

Split the signature into `bands` bands of `rows` rows. Two documents become
candidates if ANY band matches exactly. The probability of that is
`1 - (1 - s**rows)**bands` for a true Jaccard `s`, which is steep: a threshold
you choose, not a threshold you hope for.
"""

from __future__ import annotations

from dataclasses import dataclass

from .minhash import MinHashError


class LshError(ValueError):
    """A banding that cannot be built from the signature it is given."""


@dataclass(frozen=True)
class Bands:
    """A banding of a signature: `bands * rows` positions, used in order."""

    bands: int
    rows: int

    def __post_init__(self) -> None:
        if self.bands < 1:
            raise LshError(f"a banding needs at least one band, not {self.bands}")
        if self.rows < 1:
            raise LshError(f"a band needs at least one row, not {self.rows}")

    @property
    def width(self) -> int:
        return self.bands * self.rows

    def probability(self, similarity: float) -> float:
        """The chance that two documents with this similarity share a band."""
        if not 0.0 <= similarity <= 1.0:
            raise LshError(f"a similarity is a number in 0..1, not {similarity}")
        return 1.0 - (1.0 - similarity**self.rows) ** self.bands

    def curve(self, points: int = 11) -> list[tuple[float, float]]:
        if points < 2:
            raise LshError(f"a curve needs at least two points, not {points}")
        return [
            (index / (points - 1), self.probability(index / (points - 1)))
            for index in range(points)
        ]

    def threshold(self) -> float:
        """The similarity at which exactly half the true pairs become candidates.

        Solving `1 - (1 - s**rows)**bands = 1/2` for `s` gives
        `(1 - 0.5**(1/bands))**(1/rows)`. The familiar `(1/bands)**(1/rows)` is the
        rougher estimate that ignores the half inside the bracket, and it lands a
        couple of points high, where the curve is already well past a half.
        """
        return (1.0 - 0.5 ** (1.0 / self.bands)) ** (1.0 / self.rows)

    def buckets(self, signature: tuple[int, ...]) -> list[tuple[int, tuple[int, ...]]]:
        """The band keys of one signature, which are what a hash table would store."""
        if len(signature) < self.width:
            raise LshError(
                f"a {self.bands}x{self.rows} banding needs {self.width} positions "
                f"but the signature has {len(signature)}"
            )
        return [
            (band, tuple(signature[band * self.rows : (band + 1) * self.rows]))
            for band in range(self.bands)
        ]

    def candidates(self, signatures: dict[str, tuple[int, ...]]) -> list[tuple[str, str]]:
        """Every pair of names that shares at least one band, each pair once, sorted."""
        table: dict[tuple[int, tuple[int, ...]], list[str]] = {}
        for name, signature in signatures.items():
            for key in self.buckets(signature):
                table.setdefault(key, []).append(name)
        pairs: set[tuple[str, str]] = set()
        for names in table.values():
            if len(names) < 2:
                continue
            ordered = sorted(names)
            for first in range(len(ordered)):
                for second in range(first + 1, len(ordered)):
                    pairs.add((ordered[first], ordered[second]))
        return sorted(pairs)

    def describe(self) -> str:
        return f"{self.bands} band(s) of {self.rows} row(s), {self.width} positions"


def pick(width: int, threshold: float = 0.8) -> Bands:
    """The divisor pair of `width` whose S-curve passes closest to half at `threshold`."""
    if width < 1:
        raise MinHashError(f"a signature needs at least one position, not {width}")
    if not 0.0 < threshold < 1.0:
        raise LshError(f"a threshold is a similarity in 0..1, not {threshold}")
    best: tuple[float, Bands] | None = None
    for bands in range(1, width + 1):
        if width % bands:
            continue
        candidate = Bands(bands, width // bands)
        distance = abs(candidate.probability(threshold) - 0.5)
        if best is None or distance < best[0]:
            best = (distance, candidate)
    if best is None:
        raise LshError(f"no banding fits {width} positions")
    return best[1]
