"""Six stories about counts, rows, and what a min owes the truth.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .brute import min_of_rows, true_counts
from .corpus import synthetic
from .hashes import bijective
from .sketch import CountMinSketch


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the sketch makes, each computed fresh."""
    told: list[Story] = []

    events = synthetic(120, seed=9)
    sketch = CountMinSketch()
    for key, n in events:
        sketch.add(key, n)
    truth = true_counts(events)
    never_under = all(
        sketch.count(key) >= exact for key, exact in truth.items()
    )
    told.append(
        Story(
            "the min of rows never dips under the truth",
            f"{len(events)} adds, {len(truth)} tracked, "
            f"{sum(1 for k in truth if sketch.count(k) == truth[k])} exact",
            never_under,
        )
    )

    bare = CountMinSketch()
    told.append(
        Story(
            "an empty sketch counts zero for every key",
            f"count(7) on a fresh grid is {bare.count(7)}",
            bare.count(7) == 0,
        )
    )

    first = CountMinSketch()
    for key, n in events:
        first.add(key, n)
    second = CountMinSketch()
    for key, n in events:
        second.add(key, n)
    same = all(first.count(key) == second.count(key) for key in truth)
    told.append(
        Story(
            "same stream, same seed, same answers",
            f"{len(truth)} tracked counts replayed identically",
            same,
        )
    )

    told.append(
        Story(
            "every shipped row is a bijection on the cells",
            f"width {sketch.width}, multipliers {sketch.multipliers}",
            bijective(sketch.width, sketch.multipliers),
        )
    )

    cells = sketch.cells_of(42)
    answer = sketch.count(42)
    told.append(
        Story(
            "the answer is the min of the cells a key visits",
            f"cells {cells} -> min {answer}",
            answer == min_of_rows(sketch.rows, cells),
        )
    )
    exact_all = all(sketch.count(k) == truth[k] for k in truth)
    told.append(
        Story(
            "the shipped grid answers the shipped stream exactly",
            f"{len(truth)} keys, drift {sum(1 for k in truth if sketch.count(k) > truth[k])}",
            exact_all,
        )
    )
    return told
