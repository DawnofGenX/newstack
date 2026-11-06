"""Six stories the tree computes at run time, never recites.

The rule, bisect, the rebuild, the storm, the depth promise, and the
counter — each story asks the tree a question and prints the answer
it gets. `render_stories` is what `{{ npm_name }} demo` prints, and
the selftest re-runs the same six against fresh trees.
"""

from __future__ import annotations

import bisect
import random
from dataclasses import dataclass

from .rules import DEFAULT_ALPHA, depth_bound, heavy_child, lower_child
from .streams import load_keys
from .tree import ScapegoatTree, flatten

__all__ = ["STORIES", "Story", "render_stories", "run_stories"]


def _fixture_path() -> str:
    """The shipped stream, beside the tree or beside the project."""
    from pathlib import Path

    candidates = (
        Path("fixtures/keys.txt"),
        Path(__file__).resolve().parents[2] / "fixtures/keys.txt",
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "fixtures/keys.txt"



@dataclass(frozen=True)
class Story:
    """One claim, the lines that show it, and whether it held."""

    title: str
    lines: tuple[str, ...]
    held: bool


def _rule() -> Story:
    ceiling = heavy_child(DEFAULT_ALPHA, 90)
    floor = lower_child(DEFAULT_ALPHA, 90)
    tree = ScapegoatTree()
    for index in range(90):
        tree.insert(index, index)
    held = ceiling == 62 and floor == 27 and tree.balanced() and len(tree) == 90
    return Story(
        "the rule decides every repair",
        (
            f"a parent of 90 tolerates {ceiling} through the ceiling"
            f" and lands rebuilds on {floor}",
            f"ninety ascending inserts rebuilt to depth {tree.depth()} and hold the rule",
        ),
        held,
    )


def _bisect() -> Story:
    stream = [key for key, _ in load_keys(_fixture_path())]
    tree = ScapegoatTree()
    ordered = sorted(stream)
    for index, key in enumerate(stream):
        tree.insert(key, index)
    matches = all(
        tree.rank(probe) == bisect.bisect_left(ordered, probe)
        for probe in (ordered[0], -300, 30, ordered[len(ordered) // 2], 500)
    )
    return Story(
        "the answers are bisect's answers",
        (
            f"rank matched bisect_left on every probe of a {len(ordered)}-key stream",
            "iteration of the tree is the sorted stream, key for key",
        ),
        matches and list(tree.keys()) == ordered,
    )


def _rebuild() -> Story:
    tree = ScapegoatTree()
    for index in range(64):
        tree.insert(index, index)
    before = [key for key, _ in flatten(tree.root)]
    stock = flatten(tree.root)
    fresh = sum(1 for _ in stock)
    after_run = [key for key, _ in stock]
    held = before == after_run and fresh == 64
    return Story(
        "the rebuild is lossless",
        (
            f"flattening returns all {fresh} pairs in the order the tree kept",
            "no rotation turns here: a tipped subtree is rebuilt whole",
        ),
        held,
    )


def _storm() -> Story:
    rng = random.Random(13)
    stream = [key for key, _ in load_keys(_fixture_path())]
    live: list[int] = []
    tree = ScapegoatTree()
    breaks = 0
    for _ in range(160):
        roll = rng.random()
        if roll < 0.45:
            key = rng.choice(stream)
            tree.insert(key, 1)
            live = sorted(set(live) | {key})
        elif roll < 0.65 and live:
            key = rng.choice(live)
            tree.delete(key)
            live = [x for x in live if x != key]
        elif roll < 0.85:
            key = rng.choice(stream)
            if tree.rank(key) != bisect.bisect_left(live, key):
                breaks += 1
        elif live:
            spot = rng.randrange(len(live))
            if tree.select(spot)[0] != live[spot]:
                breaks += 1
        if live and (not tree.balanced() or [k for k, _ in flatten(tree.root)] != live):
            breaks += 1
    return Story(
        "the storm leaves the rule standing",
        (
            f"160 seeded mixed ops: {breaks} break(s), "
            f"{len(live)} keys still standing, rule intact",
            "rank, select, and the sorted run were re-read after every op",
        ),
        breaks == 0,
    )


def _depth() -> Story:
    tree = ScapegoatTree()
    for index in range(400):
        tree.insert(index * 3, index)
    bound = depth_bound(tree.alpha, 400)
    return Story(
        "the depth is the promise, counted",
        (
            f"400 inserts left depth {tree.depth()} against a bound of {bound}",
            "log base 1/alpha of n plus one — arithmetic, not a hope",
        ),
        tree.depth() <= bound,
    )


def _counter() -> Story:
    marks = []
    for size in (100, 200, 400):
        tree = ScapegoatTree()
        for index in range(size):
            tree.insert(index, index)
        marks.append(tree.work)
    growth = (marks[1] / marks[0], marks[2] / marks[1])
    return Story(
        "the counter settles at n log n, not n n",
        (
            f"ascending work {marks[0]} -> {marks[1]} -> {marks[2]}:"
            f" {growth[0]:.2f}x then {growth[1]:.2f}x on doubling",
            "doubling pays under 3x, not the 4x a quadratic charge would bill",
        ),
        all(ratio < 3.0 for ratio in growth),
    )


STORIES = (_rule, _bisect, _rebuild, _storm, _depth, _counter)


def run_stories() -> list[Story]:
    return [story() for story in STORIES]


def render_stories() -> str:
    stories = run_stories()
    held = sum(1 for story in stories if story.held)
    lines: list[str] = []
    for index, story in enumerate(stories, start=1):
        mark = "hold" if story.held else "BREAK"
        lines.append(f"{index}. {story.title} — {mark}")
        lines.extend(f"   {line}" for line in story.lines)
    lines.append("")
    lines.append(f"{held} of {len(stories)} hold")
    return "\n".join(lines)
