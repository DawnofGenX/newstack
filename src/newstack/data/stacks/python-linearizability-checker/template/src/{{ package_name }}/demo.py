"""Six histories, each with a claim the demo checks while it prints.

The claims are the point. A checker that says "not linearizable" and cannot show
what would have made it linearizable is only slightly more useful than a guess.
"""

from __future__ import annotations

from .check import brute_force, check, is_minimal, shrink
from .explain import verdict_lines
from .history import READ, WRITE, History, Operation


class Story:
    def __init__(self, title: str) -> None:
        self.title = title
        self.lines: list[str] = []
        self.held = True

    def say(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def require(self, claim: str, holds: bool) -> None:
        mark = "ok  " if holds else "FAIL"
        self.lines.append(f"  {mark} {claim}")
        self.held = self.held and holds

    def block(self, lines: list[str]) -> None:
        self.lines.extend(f"  {line}" for line in lines)


def _op(client: int, kind: str, value: int, start: int, end: int) -> Operation:
    return Operation(client=client, kind=kind, value=value, start=start, end=end)


def story_sequential() -> Story:
    story = Story("a sequential history has one order")
    history = History(
        (
            _op(0, WRITE, 5, 0, 2),
            _op(0, READ, 5, 3, 4),
            _op(0, WRITE, 7, 5, 6),
        ),
        initial=0,
    )
    outcome = check(history)
    story.say("one client, three operations, no overlap in time")
    story.block(verdict_lines(history, outcome))
    story.require("the history is linearizable", outcome.linearizable)
    story.require("the witness is the only order there is", outcome.order == (0, 1, 2))
    return story


def story_invented_value() -> Story:
    story = Story("a read of a value nobody wrote is wrong on its own")
    history = History((_op(0, WRITE, 5, 0, 2), _op(1, READ, 3, 3, 4)), initial=0)
    outcome = check(history)
    story.say("a write of 5 completes at instant 2; a read returns 3 at instant 4")
    story.say("3 was never written, so no order of these operations explains it")
    story.block(verdict_lines(history, outcome))
    core, _ = shrink(history)
    story.require("the checker refuses it", not outcome.linearizable)
    story.require("the core is the read alone", len(core) == 1 and core.operations[0].kind == READ)
    story.require("the write is not needed to explain the refusal", len(core) < len(history))
    return story


def story_reads_inside_a_write() -> Story:
    story = Story("two reads may straddle a write")
    history = History(
        (
            _op(0, WRITE, 1, 0, 10),
            _op(1, READ, 0, 1, 2),
            _op(1, READ, 1, 3, 4),
        ),
        initial=0,
    )
    outcome = check(history)
    story.say("the write overlaps both reads, so the linearization may put it between them")
    story.block(verdict_lines(history, outcome))
    story.require("the history is linearizable", outcome.linearizable)
    story.require("the write sits between the two reads", outcome.order == (1, 0, 2))
    return story


def story_after_the_response() -> Story:
    story = Story("a read that starts after the response must see the write")
    history = History((_op(0, WRITE, 5, 0, 2), _op(1, READ, 0, 3, 4)), initial=0)
    outcome = check(history)
    story.say("the read invokes at 3, after the write responded at 2")
    story.block(verdict_lines(history, outcome))
    story.require("the checker refuses the read-before-write order", not outcome.linearizable)

    overlapping = History((_op(0, WRITE, 5, 0, 2), _op(1, READ, 0, 1, 4)), initial=0)
    moved = check(overlapping)
    story.say("move the same read's invocation to 1 and the two overlap")
    story.require("now reading the old value is legal", moved.linearizable)
    story.require("and the read is linearized first", moved.order == (1, 0))

    only_write = History((_op(0, WRITE, 5, 0, 2),), initial=0)
    only_read = History((_op(1, READ, 0, 3, 4),), initial=0)
    core, _ = shrink(history)
    story.require("the write alone is linearizable", check(only_write).linearizable)
    story.require("the read alone is linearizable", check(only_read).linearizable)
    story.require("so the core is the pair, not either half", len(core) == 2 and is_minimal(core))
    return story


def story_shrink() -> Story:
    story = Story("the counterexample is smaller than the history it came from")
    operations = (
        _op(0, WRITE, 1, 0, 1),
        _op(1, READ, 0, 2, 3),
        _op(2, WRITE, 9, 4, 5),
        _op(1, READ, 9, 6, 7),
        _op(3, READ, 1, 8, 9),
    )
    history = History(operations, initial=0)
    outcome = check(history)
    story.say("five operations; the checker drops them one at a time while the rest stays refused")
    story.block(verdict_lines(history, outcome))
    core, verdict = shrink(history)
    story.require("the history is not linearizable", not outcome.linearizable)
    story.require("the core is smaller than the history", len(core) < len(history))
    story.require("and every operation in the core is needed", is_minimal(core))
    story.require("the core is still refused", not verdict.linearizable)
    return story


def story_pruning() -> Story:
    story = Story("the pruning is what makes the search finish")
    history = History(
        (
            _op(0, WRITE, 1, 0, 1),
            _op(1, READ, 1, 2, 3),
            _op(2, WRITE, 2, 2, 4),
            _op(3, READ, 2, 5, 6),
            _op(4, WRITE, 3, 5, 7),
            _op(5, READ, 3, 8, 9),
            _op(6, READ, 0, 0, 0),
        ),
        initial=0,
    )
    outcome = check(history)
    slow = brute_force(history)
    story.say(f"seven operations: {len(history)}! = 5040 orders to try one at a time")
    story.say(f"the search settled it in {outcome.nodes} node(s), the yardstick in {slow.nodes}")
    story.require("both agree it is linearizable", outcome.linearizable == slow.linearizable)
    story.require("both found the same witness order", outcome.order == slow.order)
    story.require("the search visited far fewer nodes", outcome.nodes * 10 < slow.nodes)
    story.require(
        "and the memo never had to fire on a first-solution search", outcome.memo_hits == 0
    )
    return story


STORIES = (
    story_sequential,
    story_invented_value,
    story_reads_inside_a_write,
    story_after_the_response,
    story_shrink,
    story_pruning,
)


def run_stories() -> list[Story]:
    return [make() for make in STORIES]


def render_stories() -> list[str]:
    lines: list[str] = []
    total = 0
    held = 0
    for number, story in enumerate(run_stories(), start=1):
        total += 1
        held += 1 if story.held else 0
        lines.append(f"{number}. {story.title}")
        lines.extend(story.lines)
        lines.append("")
    verdict = "hold" if held == total else "BROKEN"
    lines.append(f"stories      {held} of {total} {verdict}")
    return lines
