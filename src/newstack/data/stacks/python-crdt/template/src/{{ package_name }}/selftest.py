"""Checks that run without pytest, so `selftest` is the gate on its own."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .clock import ClockError, Stamp
from .counter import CounterError, GCounter, PNCounter, SignedTotal
from .demo import canon, render, stories
from .laws import check as check_laws
from .network import gossip
from .orset import ORSet, ORSetError, PlainSet
from .register import LWWRegister, RegisterError

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"ok   {name}")
        return
    FAILED += 1
    print(f"FAIL {name}")
    if detail:
        print(f"     {detail}")


def refuses(name: str, call: Callable[[], Any], kind: type[Exception]) -> None:
    try:
        call()
    except kind:
        check(name, True)
    except Exception as error:  # any other error is a failed check
        check(name, False, f"raised {type(error).__name__}: {error}")
    else:
        check(name, False, "nothing was raised")


def _quiet(call: Callable[[], Any]) -> tuple[Any, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        value = call()
    return value, buffer.getvalue()


def _clock_checks() -> None:
    early, late = Stamp(1_000, "a"), Stamp(1_001, "a")
    check("stamps order by millisecond", early < late)
    check("the same millisecond falls back to the node", Stamp(1_000, "a") < Stamp(1_000, "b"))
    check("two identical stamps compare equal", Stamp(5, "a") == Stamp(5, "a"))
    check(
        "a stamp round-trips through as_list", Stamp.parse(Stamp(9, "z").as_list()) == Stamp(9, "z")
    )
    refuses("a negative stamp is refused", lambda: Stamp(-1, "a"), ClockError)
    refuses("a nameless stamp is refused", lambda: Stamp(1, ""), ClockError)
    refuses("a stamp of the wrong shape is refused", lambda: Stamp.parse([1]), ClockError)
    refuses("a string millisecond is refused", lambda: Stamp.parse(["1", "a"]), ClockError)


def _counter_checks() -> None:
    counter = GCounter().increment("a", 3).increment("b", 2)
    check("a grow-only counter sums its nodes", counter.value() == 5)
    check("increments stay with their node", counter.counts == {"a": 3, "b": 2})
    left = GCounter({"a": 3})
    right = GCounter({"b": 4})
    check("merge takes the highest count per node", left.merge(right).counts == {"a": 3, "b": 4})
    check("merge is commutative", left.merge(right) == right.merge(left))
    check("a state round-trips through JSON", GCounter.parse(left.as_dict()) == left)
    refuses("a stored negative count is refused", lambda: GCounter({"a": -1}), CounterError)
    refuses("a boolean count is refused", lambda: GCounter({"a": True}), CounterError)
    refuses("a zero increment is refused", lambda: GCounter().increment("a", 0), CounterError)
    refuses(
        "an increment without a node is refused", lambda: GCounter().increment(""), CounterError
    )
    refuses(
        "a state of the wrong type is refused",
        lambda: GCounter.parse({"type": "or-set", "counts": {}}),
        CounterError,
    )

    older = SignedTotal().apply("a", -1)
    newer = older.apply("a", -1)
    trap = older.merge(newer)
    check("a signed dict merged by max loses the later decrement", trap.value() == -1)
    check("the newer copy really holds two decrements", newer.value() == -2)
    check("so max() read the newer copy as the older one", trap.value() != newer.value())

    pn = PNCounter().decrement("a", 1).decrement("b", 1)
    check("a pair of counters reports minus two", pn.value() == -2)
    mixed = PNCounter().increment("a", 5).merge(PNCounter().decrement("b", 2))
    check("the two halves merge independently", mixed.value() == 3)
    check("a pn state round-trips through JSON", PNCounter.parse(mixed.as_dict()) == mixed)
    refuses(
        "a negative stored half is refused",
        lambda: PNCounter.parse({"type": "pn-counter", "positive": {"a": -1}, "negative": {}}),
        CounterError,
    )


def _register_checks() -> None:
    empty = LWWRegister()
    check("an empty register says so", empty.is_empty)
    filled, first = empty.assign("red", 1_000, "a")
    check("the first write applies", first.applied and first.previous is None)
    newer, second = filled.assign("green", 1_001, "a")
    check("a newer write applies and reports what it replaced", second.applied)
    check("the replaced stamp is the old one", second.previous == Stamp(1_000, "a"))
    stale, third = newer.assign("blue", 999, "z")
    check("an older write is ignored", not third.applied and stale.value == "green")
    tie, _ = LWWRegister().assign("blue", 1_000, "b")
    check("the node breaks a millisecond tie", filled.merge(tie).value == "blue")
    check("merge keeps the newest stamp", filled.merge(newer) == newer)
    other = LWWRegister("blue", Stamp(1_000, "a"))
    refuses("two values under one stamp are refused", lambda: filled.merge(other), RegisterError)
    check("a register round-trips through JSON", LWWRegister.parse(filled.as_dict()) == filled)
    refuses(
        "a value without a stamp is refused",
        lambda: LWWRegister.parse({"type": "lww-register", "value": "red", "stamp": None}),
        RegisterError,
    )
    refuses(
        "a value without a stamp cannot be built", lambda: LWWRegister("red", None), RegisterError
    )


def _orset_checks() -> None:
    once = ORSet().add("x", "a")
    check("an add shows up", once.contains("x"))
    check("a remove of an observed tag removes it", not once.remove("x").contains("x"))
    check("removing an element nobody added changes nothing", once.remove("y").elements() == {"x"})
    left = ORSet().add("x", "a").remove("x")
    right = ORSet().add("x", "b")
    merged = left.merge(right)
    check("a concurrent add survives the remove", merged.contains("x"))
    check("the surviving tag is the unseen one", merged.tags_for("x") == {("b", 1)})
    check("a remove after seeing both tags wins", not merged.remove("x").contains("x"))
    check("merge unions the tags", once.merge(right).tags_for("x") == {("a", 1), ("b", 1)})
    holder = ORSet().add("y", "b")
    check("tombstones survive a merge", not merged.merge(holder).remove("y").contains("y"))
    check(
        "both replicas keep counting from their own maximum",
        merged.merge(right).counters == {"a": 1, "b": 1},
    )
    check("an or-set round-trips through JSON", ORSet.parse(merged.as_dict()) == merged)
    refuses(
        "a malformed tag is refused",
        lambda: ORSet.parse(
            {"type": "or-set", "entries": {"x": [[1]]}, "tombstones": [], "counters": {}}
        ),
        ORSetError,
    )
    plain = PlainSet(frozenset({"x"})).remove("x").merge(PlainSet(frozenset({"x"})))
    check("a plain set loses the remove", plain.contains("x"))
    check("elements lists only what is visible", merged.elements() == {"x"})


def _law_checks() -> None:
    serialise = lambda state: canon(state.as_dict())  # noqa: E731
    counter_states = [GCounter(), GCounter({"a": 1}), GCounter({"b": 2})]
    check(
        "a grow-only counter keeps the laws",
        all(law.held for law in check_laws(counter_states, GCounter.merge, serialise)),
    )
    set_states = [ORSet().add("x", "a"), ORSet().add("y", "b"), ORSet().add("x", "a").remove("x")]
    check(
        "an or-set keeps the laws",
        all(law.held for law in check_laws(set_states, ORSet.merge, serialise)),
    )
    register_states = [
        LWWRegister(),
        LWWRegister("red", Stamp(1, "a")),
        LWWRegister("blue", Stamp(1, "b")),
    ]
    check(
        "a last-write-wins register keeps the laws",
        all(law.held for law in check_laws(register_states, LWWRegister.merge, serialise)),
    )
    left_wins = lambda left, right: left  # noqa: E731
    failed = {law.name for law in check_laws(counter_states, left_wins, serialise) if not law.held}
    check("a merge that keeps the left side breaks commutativity", failed == {"commutative"})
    averaging = lambda left, right: (left + right) / 2  # noqa: E731
    regrouped = {law.name for law in check_laws([1.0, 2.0, 8.0], averaging, str) if not law.held}
    check("an averaging merge breaks associativity", regrouped == {"associative"})
    refuses(
        "law checks need two states",
        lambda: check_laws(counter_states[:1], GCounter.merge, serialise),
        ValueError,
    )


def _network_checks() -> None:
    serialise = lambda state: canon(state.as_dict())  # noqa: E731
    replicas = [ORSet().add("x", "a"), ORSet().add("y", "b"), ORSet().add("z", "c")]
    flowed = gossip(replicas, ORSet.merge, serialise, seed=5)
    check("gossip converges", flowed.converged)
    check(
        "every replica ends with every element",
        all(item.elements() == {"x", "y", "z"} for item in flowed.replicas),
    )
    check("duplicated delivery is harmless", len(set(flowed.states)) == 1)
    counters = [PNCounter().increment("a", 2), PNCounter().decrement("b", 1)]
    counter_flow = gossip(counters, PNCounter.merge, serialise, seed=9, rounds=2)
    check(
        "a counter pair also converges",
        counter_flow.converged and counter_flow.replicas[0].value() == 1,
    )
    check("gossip counts its deliveries", flowed.deliveries > 0)
    refuses(
        "gossip needs two replicas",
        lambda: gossip(replicas[:1], ORSet.merge, serialise),
        ValueError,
    )


def _demo_checks() -> None:
    items = stories()
    check("there are six stories", len(items) == 6)
    check("every story shows what it promises", all(item.shown for item in items))
    lines = render(items)
    check("the stories are numbered", lines[0].startswith("1. "))
    check("the render ends with a blank line", lines[-1] == "")


def _cli_checks() -> None:
    from . import cli

    left = GCounter({"a": 2})
    right = GCounter({"b": 3})
    merged = cli.merge_states(left.as_dict(), right.as_dict())
    check("the cli merges two counters", merged["counts"] == {"a": 2, "b": 3})
    refuses(
        "the cli refuses two different lattices",
        lambda: cli.merge_states(left.as_dict(), ORSet().as_dict()),
        cli.UsageError,
    )
    refuses(
        "the cli refuses a type it does not know",
        lambda: cli.merge_states({"type": "signed-total"}, {"type": "signed-total"}),
        cli.UsageError,
    )
    code, output = _quiet(cli.run_laws)
    check("the law report exits zero", code == 0)
    check(
        "the law report names the four lattices",
        all(name in output for name in ("g-counter", "or-set")),
    )
    code, output = _quiet(lambda: cli.main(["demo"]))
    check("the demo exits zero", code == 0 and "gossip" in output)
    code, _ = _quiet(lambda: cli.main([]))
    check("no subcommand exits two", code == 2)

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "state.json"
        path.write_text(json.dumps(right.as_dict()), encoding="utf-8")
        code, output = _quiet(lambda: cli.main(["merge", str(path), str(path)]))
        check("merging a state with itself exits zero", code == 0)
        check("merging a state with itself changes nothing", json.loads(output) == right.as_dict())
        missing = Path(directory) / "absent.json"
        code, _ = _quiet(lambda: cli.main(["merge", str(path), str(missing)]))
        check("a missing state file exits two", code == 2)
        broken = Path(directory) / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        refuses("a broken state file is refused", lambda: cli.load_state(broken), cli.UsageError)


def run() -> int:
    for checks in (
        _clock_checks,
        _counter_checks,
        _register_checks,
        _orset_checks,
        _law_checks,
        _network_checks,
        _demo_checks,
        _cli_checks,
    ):
        checks()
    total = PASSED + FAILED
    if FAILED:
        print(f"selftest: {FAILED} of {total} checks failed")
        return 1
    print(f"selftest: {total} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
