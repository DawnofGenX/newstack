"""Measurement helpers: a stream with a known truth, and the error against it."""

from __future__ import annotations

from dataclasses import dataclass

from .sketch import CountMinSketch


def skewed_counts(items: int = 300, scale: int = 20_000) -> dict[str, int]:
    """A deterministic Zipf-shaped stream: the truth is a dict, not a sample."""
    if items < 1:
        raise ValueError(f"items must be at least 1, not {items}")
    counts: dict[str, int] = {}
    for rank in range(1, items + 1):
        counts[f"user:{rank:04d}"] = max(1, round(scale / rank))
    return counts


def feed(
    sketch: CountMinSketch, counts: dict[str, int], *, conservative: bool | None = None
) -> None:
    """Add every item `counts[item]` times, in rank order."""
    for item, count in counts.items():
        for _ in range(count):
            sketch.add(item)


@dataclass(frozen=True)
class Report:
    total: int
    items: int
    underestimates: int
    max_over: int
    mean_over: float
    worst: str
    bound: float

    @property
    def held(self) -> bool:
        return self.underestimates == 0 and self.max_over <= self.bound

    def lines(self) -> list[str]:
        return [
            f"  updates            {self.total}",
            f"  distinct items     {self.items}",
            f"  underestimates     {self.underestimates}",
            f"  largest overestimate {self.max_over}",
            f"  mean overestimate  {self.mean_over:.2f}",
            f"  worst item         {self.worst}",
            f"  promise            {self.bound:.1f}",
        ]


def report(sketch: CountMinSketch, counts: dict[str, int]) -> Report:
    if not counts:
        raise ValueError("there is nothing to compare against")
    over = {item: sketch.estimate(item) - true for item, true in counts.items()}
    worst = max(over, key=lambda item: over[item])
    return Report(
        total=sketch.total,
        items=len(counts),
        underestimates=sum(1 for value in over.values() if value < 0),
        max_over=max(over.values()),
        mean_over=sum(over.values()) / len(over),
        worst=worst,
        bound=sketch.bound(),
    )


def filled(
    counts: dict[str, int], width: int, depth: int, *, conservative: bool = False
) -> CountMinSketch:
    sketch = CountMinSketch(width, depth, conservative=conservative)
    feed(sketch, counts)
    return sketch


def top(
    sketch: CountMinSketch, counts: dict[str, int], amount: int = 5
) -> list[tuple[str, int, int]]:
    """The sketch's top `amount` items, with the true count beside each estimate."""
    ranked = sorted(counts, key=lambda item: (-sketch.estimate(item), item))
    return [(item, sketch.estimate(item), counts[item]) for item in ranked[:amount]]
