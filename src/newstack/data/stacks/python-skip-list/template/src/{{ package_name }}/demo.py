"""Six stories about staying sorted one coin flip at a time.

Nothing here is a picture of the algorithm; every claim is a comparison
the demo computes against `bisect` or against a twin map, and `stories`
reports whether all of them held.
"""

from __future__ import annotations

import bisect

from .coins import DEFAULT_SEED, expected_level
from .map import SkipList
from .stack import synthetic

__all__ = ["Story", "render_stories", "stories"]

DEMO_CORPUS = 400
DEMO_SEED = 11


class Story:
    """One story: a claim, the lines that argue for it, and the checks that hold it up."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.lines: list[str] = []
        self.checks: list[tuple[str, bool]] = []

    def say(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def block(self, lines: list[str]) -> None:
        for line in lines:
            self.lines.append(f"  {line}")

    def require(self, claim: str, held: bool) -> None:
        self.checks.append((claim, bool(held)))
        mark = "ok  " if held else "FAIL"
        self.lines.append(f"  {mark} {claim}")

    @property
    def held(self) -> bool:
        return all(held for _, held in self.checks) and bool(self.checks)

    def render(self) -> list[str]:
        return [self.title, *self.lines]


def _filled(seed: int = DEMO_SEED) -> tuple[SkipList, list[int]]:
    """The demo map and the sorted list `bisect` is asked about."""
    pairs = synthetic(DEMO_CORPUS, seed=seed)
    filled = SkipList(seed=DEFAULT_SEED)
    for key, value in pairs:
        filled.insert(key, value)
    return filled, sorted(key for key, _ in pairs)


def _story_rank() -> Story:
    story = Story("1. rank agrees with bisect, key by key")
    filled, ordered = _filled()
    probes = [*ordered[:: len(ordered) // 20], ordered[0], ordered[-1]]
    mismatch = sum(
        1 for probe in probes if filled.rank(probe) != bisect.bisect_left(ordered, probe)
    )
    story.say(f"{len(filled)} keys stored, {len(probes)} probes against bisect:")
    story.say(f"  mismatches {mismatch}")
    story.require("rank answers exactly what bisect answers", mismatch == 0)
    story.require(
        "rank of the smallest key is zero", filled.rank(ordered[0]) == 0
    )
    story.require(
        "rank past the largest is the whole map",
        filled.rank(ordered[-1] + 1) == len(filled),
    )
    return story


def _story_inverse() -> Story:
    story = Story("2. select and rank are exact inverses")
    filled, ordered = _filled()
    forward = all(filled.rank(key) == index for index, key in enumerate(ordered))
    back = all(filled.rank(filled.select(index)[0]) == index for index in range(len(filled)))
    story.say(f"{len(filled)} positions walked both ways:")
    story.say(f"  rank-then-select and select-then-rank both round-trip: {forward and back}")
    story.require("select lands where rank sent the question", forward)
    story.require("rank sends select back to the position it came from", back)
    return story


def _story_determinism() -> Story:
    story = Story("3. same seed, same tower, byte for byte")
    left, _ = _filled()
    right, _ = _filled()
    twin = left.rebuild()
    story.say("Two maps built from one seed, and one rebuilt from its pairs:")
    story.block(
        [
            f"  first  tallest {left.stats()['tallest']} height {left.height}",
            f"  second tallest {right.stats()['tallest']} height {right.height}",
            f"  rebuilt tallest {twin.stats()['tallest']} height {twin.height}",
        ]
    )
    story.require(
        "the same seed leaves the same shape",
        left.stats()["levels"] == right.stats()["levels"],
    )
    story.require(
        "replaying the pairs replays the shape",
        twin.stats()["levels"] == left.stats()["levels"],
    )
    story.require("the rebuilt map answers the same questions", twin.pairs() == left.pairs())
    return story


def _story_seeds() -> Story:
    story = Story("4. a different seed shuffles the shape, never the order")
    left, _ = _filled()
    other = SkipList(seed=DEFAULT_SEED + 1)
    for key, value in left.pairs():
        other.insert(key, value)
    story.say("One sorted list, two seeds, two shapes:")
    story.block(
        [
            f"  seed {left.seed} tallest {left.stats()['tallest']}",
            f"  seed {other.seed} tallest {other.stats()['tallest']}",
        ]
    )
    story.require("both maps hold the same pairs", other.pairs() == left.pairs())
    story.require(
        "the coin streams left different shapes",
        other.stats()["levels"] != left.stats()["levels"],
    )
    return story


def _story_delete() -> Story:
    story = Story("5. a delete repairs every width it broke")
    filled, ordered = _filled()
    doomed = ordered[::3]
    for key in doomed:
        filled.delete(key)
    survived = [key for key in ordered if key not in set(doomed)]
    mismatch = sum(
        1 for probe in survived[::10] if filled.rank(probe) != bisect.bisect_left(survived, probe)
    )
    story.say(f"{len(doomed)} towers knocked down, widths re-summed:")
    story.say(f"  size now {len(filled)}, bisect mismatches {mismatch}")
    story.require("the map shrank by exactly the deletions", len(filled) == len(survived))
    story.require("rank still answers what bisect answers", mismatch == 0)
    story.require("iteration is still the sorted order", list(filled.keys()) == survived)
    return story


def _story_shape() -> Story:
    story = Story("6. the towers stay as short as log2 promises")
    filled, _ = _filled()
    stats = filled.stats()
    tallest = int(stats["tallest"])
    expected = expected_level(len(filled))
    levels = list(stats["levels"])
    story.say(f"{len(filled)} keys, log2 says about {expected} stories:")
    story.block(
        [
            f"  tallest  {tallest} stories",
            f"  flips    {stats['flips']} coin flips spent",
            f"  levels   {' '.join(str(count) for count in levels[:8])} ...",
        ]
    )
    story.require("the tallest tower is within the log2 promise", tallest <= expected + 3)
    story.require("level counts fall as levels climb", levels[0] > levels[1] > levels[2])
    story.require("the map paid for its shape in flips", stats["flips"] >= len(filled))
    return story


def stories() -> list[Story]:
    return [
        _story_rank(),
        _story_inverse(),
        _story_determinism(),
        _story_seeds(),
        _story_delete(),
        _story_shape(),
    ]


def render_stories() -> str:
    told = stories()
    lines: list[str] = []
    for story in told:
        lines.extend(story.render())
        lines.append("")
    held = sum(1 for story in told if story.held)
    if held == len(told):
        lines.append(f"stories      {held} of {len(told)} hold")
    else:
        lines.append(f"stories      BROKEN: {held} of {len(told)} hold")
    return "\n".join(lines)
