"""Fold readings of a monotonic counter into windows you can defend."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from itertools import pairwise

from .model import Rollup, RollupError, Sample, Window, delta_for, window_of


def rollup(
    samples: Iterable[Sample],
    width_us: int,
    *,
    name: str,
    shard: str = "default",
) -> list[Rollup]:
    """Sum the increases between consecutive readings into aligned windows.

    An increase belongs to the window containing the LATER reading: a scrape
    interval that straddles a boundary is one measurement, and splitting it would
    invent two numbers nobody measured. The cost is that a window's coverage can
    begin before its own start, which is why `covered_us` is reported.
    """
    readings = list(samples)
    if any(right.at_us < left.at_us for left, right in pairwise(readings)):
        raise RollupError(
            "readings arrived out of order; a counter read twice cannot be read backwards"
        )
    buckets: dict[int, list[Rollup]] = {}
    for previous, current in pairwise(readings):
        amount, reset = delta_for(previous, current)
        window = window_of(current.at_us, width_us)
        buckets.setdefault(window.start_us, []).append(
            Rollup(
                name=name,
                shard=shard,
                window=window,
                total=amount,
                samples=1,
                resets=1 if reset else 0,
                first_us=previous.at_us,
                last_us=current.at_us,
            )
        )
    rolled = [_folder(pieces) for _, pieces in sorted(buckets.items())]
    return rolled


def _folder(pieces: Sequence[Rollup]) -> Rollup:
    head = pieces[0]
    return Rollup(
        name=head.name,
        shard=head.shard,
        window=head.window,
        total=sum(piece.total for piece in pieces),
        samples=sum(piece.samples for piece in pieces),
        resets=sum(piece.resets for piece in pieces),
        first_us=min(piece.first_us for piece in pieces),
        last_us=max(piece.last_us for piece in pieces),
    )


def gaps(rollups: Sequence[Rollup], width_us: int) -> list[Window]:
    """The windows inside the observed range that no rollup covers.

    An empty window is absent, not zero: nobody scraped, so nothing is known
    about the traffic that happened in it.
    """
    if len(rollups) < 2:
        return []
    seen = {piece.window.start_us for piece in rollups}
    first = min(seen)
    last = max(seen)
    missing: list[Window] = []
    start = first
    while start <= last:
        if start not in seen:
            missing.append(Window(start_us=start, end_us=start + width_us))
        start += width_us
    return missing


def rate_per_second(rollups: Sequence[Rollup]) -> float:
    """The rate over the windows that actually observed something."""
    total = sum(piece.total for piece in rollups)
    covered = sum(piece.covered_us for piece in rollups)
    if covered == 0:
        raise RollupError(
            "no window covers any time, so the only honest rate is unknown, not zero"
        )
    return total * 1_000_000 / covered


def parse_line(number: int, text: str) -> Sample:
    """One JSONL reading: `{"at_us": 0, "value": 10}`."""
    import json

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise RollupError(f"line {number} is not JSON: {error}") from None
    if not isinstance(payload, dict):
        raise RollupError(f"line {number} is not an object")
    try:
        return Sample(at_us=payload["at_us"], value=payload["value"])
    except KeyError as error:
        raise RollupError(f"line {number} is missing {error.args[0]!r}") from None
    except TypeError as error:
        raise RollupError(f"line {number}: {error}") from None
