"""Four scenarios that show what the numbers can and cannot answer."""

from __future__ import annotations

from dataclasses import dataclass

from .merge import combine, merge
from .model import Conflict, Rollup, Sample
from .rollup import gaps, rate_per_second, rollup

WIDTH = 10 * 1_000_000
SHARD = "a"


@dataclass(frozen=True)
class Step:
    scenario: str
    lines: list[str]
    ok: bool

    def render(self) -> str:
        verdict = "as advertised" if self.ok else "NOT as advertised"
        body = "".join(f"  {line}\n" for line in self.lines)
        return f"{self.scenario:<34} {verdict}\n{body}"


def _readings(pairs: list[tuple[int, int]]) -> list[Sample]:
    return [Sample(at_us=at * 1_000_000, value=value) for at, value in pairs]


def _steady() -> Step:
    rolled = rollup(_readings([(0, 0), (10, 100), (20, 200), (30, 300)]), WIDTH, name="requests")
    rate = rolled[0].rate_per_second() if rolled else 0.0
    ok = (
        len(rolled) == 3
        and all(piece.total == 100 for piece in rolled)
        and abs(rate - 10.0) < 1e-9
        and rolled[0].window.start_us == WIDTH
    )
    return Step(
        "a steady counter",
        [
            f"windows reported: {len(rolled)} of the 4 the timeline touches",
            f"first window starts at {rolled[0].window.start_us} us, not 0: the reading at 0 "
            "is a level, and a level is not a rate",
            f"rate over the measured windows: {rate:.3f}/s",
        ],
        ok,
    )


def _reset() -> Step:
    rolled = rollup(
        _readings([(0, 500), (10, 600), (20, 20), (30, 120)]), WIDTH, name="requests"
    )
    middle = rolled[1]
    ok = (
        len(rolled) == 3
        and middle.total == 20
        and middle.resets == 1
        and all(piece.total >= 0 for piece in rolled)
    )
    return Step(
        "a counter that restarts",
        [
            f"the window after the restart reports {middle.total}, not "
            f"{20 - 600} and not nothing",
            f"resets counted: {middle.resets}",
            "a restart is a new epoch: the increase is the new value, since the old "
            "counter died at an unknown instant",
        ],
        ok,
    )


def _gap() -> Step:
    readings = _readings([(0, 0), (10, 10), (20, 20), (30, 30), (50, 50), (60, 60)])
    rolled = rollup(readings, WIDTH, name="requests")
    holes = gaps(rolled, WIDTH)
    rate = rate_per_second(rolled)
    lonely = rollup(_readings([(0, 0)]), WIDTH, name="requests")
    ok = (
        len(rolled) == 5
        and [hole.start_us // 1_000_000 for hole in holes] == [40]
        and lonely == []
        and abs(rate - 1.0) < 1e-9
    )
    return Step(
        "a scrape that never happened",
        [
            f"windows reported: {len(rolled)}; missing: "
            f"{[hole.start_us // 1_000_000 for hole in holes]} s",
            f"rate over covered time: {rate:.3f}/s: 60 events in 60 s of observation, "
            "since the interval spanning the hole is still one measurement",
            f"window 50 carries {rolled[3].total}, not 20/20 split: nobody can say which "
            "of the two windows those events happened in",
            f"a single reading yields {len(lonely)} windows, so there is no rate to invent",
        ],
        ok,
    )


def _duplicate() -> Step:
    first = rollup(_readings([(0, 0), (10, 100)]), WIDTH, name="requests")
    second = rollup(_readings([(0, 0), (10, 40)]), WIDTH, name="requests", shard="b")
    once = merge([*first, *second])
    twice = merge([*first, *second, *first])
    total_once = sum(piece.total for piece in once.rollups)
    total_twice = sum(piece.total for piece in twice.rollups)
    combined = combine(twice.rollups)
    conflicted = False
    try:
        merge([*first, *first, Rollup(
            name=first[0].name,
            shard=first[0].shard,
            window=first[0].window,
            total=first[0].total + 1,
            samples=first[0].samples,
            resets=first[0].resets,
            first_us=first[0].first_us,
            last_us=first[0].last_us,
        )])
    except Conflict:
        conflicted = True
    ok = (
        total_once == total_twice == 140
        and twice.repeated == 1
        and combined[0].total == 140
        and combined[0].shard == "*"
        and conflicted
    )
    return Step(
        "the same rollup delivered twice",
        [
            f"delivered once: {total_once}; delivered twice: {total_twice}",
            f"repeats dropped: {twice.repeated}; across shards: {combined[0].total}",
            "a repeat that disagrees raises instead of being averaged: "
            f"{'yes' if conflicted else 'no'}",
        ],
        ok,
    )


SCENARIOS = (_steady, _reset, _gap, _duplicate)


def run() -> list[Step]:
    return [builder() for builder in SCENARIOS]


def render(steps: list[Step]) -> str:
    missed = sum(1 for step in steps if not step.ok)
    body = "\n".join(step.render() for step in steps)
    return f"{body}demo: {len(steps)} scenarios, {missed} not as advertised"


def payload(steps: list[Step]) -> list[dict[str, object]]:
    return [
        {"scenario": step.scenario, "ok": step.ok, "lines": list(step.lines)}
        for step in steps
    ]
