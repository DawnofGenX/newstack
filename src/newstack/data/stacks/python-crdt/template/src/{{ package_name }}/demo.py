"""Six stories about what a merge can and cannot save."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .counter import PNCounter, SignedTotal
from .laws import check
from .network import gossip
from .orset import ORSet, PlainSet
from .register import LWWRegister


@dataclass(frozen=True)
class Story:
    """One demonstration, and whether it showed the promised behaviour."""

    title: str
    lines: list[str]
    shown: bool


def canon(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _counter_trap() -> Story:
    older = SignedTotal().apply("a", -1)
    newer = older.apply("a", -1)
    merged = older.merge(newer)
    lines = [
        "  node a decremented twice; a copy from before the second decrement arrives late",
        f"  the older copy    a={older.counts.get('a', 0)}",
        f"  the newer copy    a={newer.counts.get('a', 0)}",
        f"  merged by max     {merged.value()}",
        "  max() keeps the higher number, so it read the newer copy as the older one",
        "  a grow-only pair survives this: the decrements land in different counters",
    ]
    return Story("a counter merged by max cannot subtract", lines, merged.value() != newer.value())


def _pn_converges() -> Story:
    left = PNCounter().increment("a", 5)
    right = PNCounter().decrement("b", 2)
    flowed = gossip([left, right], PNCounter.merge, lambda state: canon(state.as_dict()), seed=3)
    lines = [
        "  replica a added five, replica b removed two, and the network duplicated every message",
        *flowed.lines(),
    ]
    value = flowed.replicas[0].value()
    return Story(
        "two grow-only counters add up instead of overwriting",
        [*lines, f"  the total          {value}"],
        flowed.converged and value == 3,
    )


def _register_drops() -> Story:
    left, _ = LWWRegister().assign("red", 1_000, "a")
    right, _ = LWWRegister().assign("blue", 1_000, "b")
    merged = left.merge(right)
    stamped = merged.stamp.text if merged.stamp else "-"
    loser = "a" if merged.value == "blue" else "b"
    lines = [
        "  both replicas wrote in the same millisecond, 1000",
        "  replica a wrote red, replica b wrote blue, neither saw the other",
        f"  merged value      {merged.value!r}, stamp {stamped}",
        f"  the write from {loser} is gone, and the register cannot even report that it went",
        "  the node name is the tiebreak, so the choice is deterministic rather than fair",
    ]
    return Story(
        "a last-write-wins register drops a concurrent write", lines, merged.value == "blue"
    )


def _plain_set_loses() -> Story:
    left = PlainSet(frozenset({"x"})).remove("x")
    right = PlainSet(frozenset({"x"}))
    merged = left.merge(right)
    lines = [
        "  replica a removed x; replica b still has it and has heard nothing about the remove",
        f"  a alone           present = {left.contains('x')}",
        f"  merged by union   present = {merged.contains('x')}",
        "  the remove vanished, and no later merge can bring it back",
    ]
    return Story(
        "a plain set loses a remove as soon as replicas diverge", lines, merged.contains("x")
    )


def _or_set_keeps() -> Story:
    left = ORSet().add("x", "a").remove("x")
    right = ORSet().add("x", "b")
    merged = left.merge(right)
    later = merged.remove("x")
    lines = [
        "  replica a added x and then removed it; replica b added x at the same time",
        f"  a alone           present = {left.contains('x')}",
        f"  merged            present = {merged.contains('x')}"
        f"  tags {sorted(merged.tags_for('x'))}",
        f"  remove again      present = {later.contains('x')}, having now seen every tag",
        "  add wins, because each remove only ever deletes the tags it has observed",
    ]
    return Story(
        "an observed-remove set keeps the add it never saw",
        lines,
        merged.contains("x") and not later.contains("x"),
    )


def _laws_and_gossip() -> Story:
    states = [
        ORSet().add("x", "a"),
        ORSet().add("y", "b").add("x", "c"),
        ORSet().add("x", "a").remove("x"),
        ORSet().add("z", "d"),
    ]
    laws = check(states, ORSet.merge, lambda state: canon(state.as_dict()))
    flowed = gossip(states, ORSet.merge, lambda state: canon(state.as_dict()), seed=11, rounds=4)
    lines = [law.line() for law in laws]
    lines.extend(flowed.lines())
    return Story(
        "the three laws are what make gossip safe",
        lines,
        all(law.held for law in laws) and flowed.converged,
    )


def stories() -> list[Story]:
    return [
        _counter_trap(),
        _pn_converges(),
        _register_drops(),
        _plain_set_loses(),
        _or_set_keeps(),
        _laws_and_gossip(),
    ]


def render(items: list[Story] | None = None) -> list[str]:
    output: list[str] = []
    for number, story in enumerate(items or stories(), start=1):
        output.append(f"{number}. {story.title}")
        output.extend(story.lines)
        output.append("")
    return output
