"""Six stories about being a heap and a search tree at once.

Nothing here is a picture of the algorithm; every claim is a comparison
the demo computes against `bisect`, against a twin tree, or against the
two orders counted node by node, and `stories` reports whether all of
them held.
"""

from __future__ import annotations

import bisect

from .draws import DEFAULT_SEED, expected_depth
from .treap import Treap
from .workload import run_workload

__all__ = ["Story", "render_stories", "stories"]

DEMO_CORPUS = 400
DEMO_SEED = 11


class Story:
    """One story: a claim, the lines that argue for it, and the checks holding it up."""

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
        return all(ok for _, ok in self.checks) and bool(self.checks)

    def render(self) -> list[str]:
        return [self.title, *self.lines]


def _filled(seed: int = DEMO_SEED) -> tuple[Treap, list[int]]:
    """The demo tree and the sorted list `bisect` is asked about."""
    from random import Random

    keys = sorted(Random(DEFAULT_SEED).sample(range(-800, 800), DEMO_CORPUS))
    tree = Treap(seed)
    for index, key in enumerate(keys):
        tree.insert(key, index)
    return tree, keys


def _story_rank() -> Story:
    story = Story("1. rank agrees with bisect, key by key")
    tree, ordered = _filled()
    probes = [*ordered[:: len(ordered) // 20], ordered[0], ordered[-1], 0, 7]
    mismatch = sum(
        1 for probe in probes if tree.rank(probe) != bisect.bisect_left(ordered, probe)
    )
    story.say(f"{len(tree)} keys stored, {len(probes)} probes against bisect:")
    story.say(f"  mismatches {mismatch}")
    story.require("rank answers exactly what bisect answers", mismatch == 0)
    story.require("rank of the smallest key is zero", tree.rank(ordered[0]) == 0)
    story.require(
        "rank past the largest is the whole tree",
        tree.rank(ordered[-1] + 1) == len(tree),
    )
    return story


def _story_inverse() -> Story:
    story = Story("2. select and rank are exact inverses")
    tree, ordered = _filled()
    forward = all(tree.rank(key) == index for index, key in enumerate(ordered))
    back = all(tree.rank(tree.select(index)[0]) == index for index in range(len(tree)))
    story.say(f"{len(tree)} positions walked both ways:")
    story.say(f"  rank-then-select and select-then-rank both round-trip: {forward and back}")
    story.require("select lands where rank sent the question", forward)
    story.require("rank sends select back to the position it came from", back)
    return story


def _story_orders() -> Story:
    story = Story("3. a mixed workload never breaks either order")
    replay = run_workload(seed=DEMO_SEED)
    story.say("160 seeded inserts, deletes, probes, and ranks:")
    story.say(f"  {replay.line()}")
    story.require("every check after every op held", replay.breaks == 0)
    story.require("the replay ran its full storm", replay.steps == 160)
    return story


def _story_split() -> Story:
    story = Story("4. a split loses nothing and a join restores it")
    tree, ordered = _filled()
    pivot = ordered[len(ordered) // 2]
    under, over = tree.split(pivot)
    left = [key for key in ordered if key < pivot]
    right = [key for key in ordered if key >= pivot]
    joined = Treap.join(under, over)
    story.say(f"cut at {pivot}: {len(under)} under, {len(over)} over")
    story.require("the left half holds exactly the keys below", list(under.keys()) == left)
    story.require("the right half holds the pivot and above", list(over.keys()) == right)
    story.require("the join restores the tree, key for key", joined.pairs() == tree.pairs())
    story.require(
        "the join even restores the shape",
        joined.stats()["walk"] == tree.stats()["walk"],
    )
    return story


def _story_seed() -> Story:
    story = Story("5. the seed owns the shape, the entries replay it")
    left, _ = _filled()
    twin = left.rebuild()
    other, _ = _filled(seed=DEFAULT_SEED + 1)
    shape_match = twin.stats()["walk"] == left.stats()["walk"]
    story.say("One tree, its rebuild from (key, priority), and another seed:")
    story.block(
        [
            f"  tree     depth {left.stats()['depth']} walk {len(left.stats()['walk'])} long",
            f"  rebuilt  depth {twin.stats()['depth']} identical: {shape_match}",
            f"  seed {other.seed}  depth {other.stats()['depth']}",
        ]
    )
    story.require("the same seed leaves the same tree", shape_match)
    story.require("another seed keeps the order", other.pairs() == left.pairs())
    story.require("another seed shuffles the shape", other.stats()["walk"] != left.stats()["walk"])
    return story


def _story_shape() -> Story:
    story = Story("6. the tree stays about as deep as the draws promise")
    tree, _ = _filled()
    stats = tree.stats()
    depth = int(stats["depth"])
    promise = expected_depth(len(tree))
    story.say(f"{len(tree)} keys, the draws stand it {depth} deep:")
    story.block(
        [
            f"  depth    {depth} against a promise near {promise}",
            f"  draws    {stats['draws']} spent on the shape",
            f"  broken   search {stats['broken'][0]}, heap {stats['broken'][1]}",
        ]
    )
    story.require("the depth stays near the drawn promise", depth <= 2 * promise + 4)
    story.require("neither order broke anywhere", stats["broken"] == (0, 0))
    story.require("the tree paid for its shape in draws", stats["draws"] >= len(tree))
    return story


def stories() -> list[Story]:
    return [
        _story_rank(),
        _story_inverse(),
        _story_orders(),
        _story_split(),
        _story_seed(),
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
