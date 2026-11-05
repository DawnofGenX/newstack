import pytest

from {{ package_name }} import counter as counters
from {{ package_name }} import laws as subject
from {{ package_name }} import orset, register


def _canon(state: object) -> str:
    import json

    return json.dumps(state.as_dict(), sort_keys=True, separators=(",", ":"))  # type: ignore[attr-defined]


def test_a_counter_keeps_the_laws() -> None:
    states = [counters.GCounter(), counters.GCounter({"a": 1}), counters.GCounter({"b": 2})]
    assert all(law.held for law in subject.check(states, counters.GCounter.merge, _canon))


def test_an_or_set_keeps_the_laws() -> None:
    states = [
        orset.ORSet().add("x", "a"),
        orset.ORSet().add("y", "b"),
        orset.ORSet().add("x", "a").remove("x"),
    ]
    assert all(law.held for law in subject.check(states, orset.ORSet.merge, _canon))


def test_a_register_keeps_the_laws() -> None:
    states = [
        register.LWWRegister(),
        register.LWWRegister("red", register.Stamp(1, "a")),
        register.LWWRegister("blue", register.Stamp(1, "b")),
    ]
    assert all(law.held for law in subject.check(states, register.LWWRegister.merge, _canon))


def test_a_merge_that_keeps_the_left_side_breaks_commutativity() -> None:
    states = [counters.GCounter(), counters.GCounter({"a": 1}), counters.GCounter({"b": 2})]
    broken = {
        law.name for law in subject.check(states, lambda left, right: left, _canon) if not law.held
    }
    assert broken == {"commutative"}


def test_an_averaging_merge_breaks_associativity() -> None:
    merge = lambda left, right: (left + right) / 2  # noqa: E731
    broken = {law.name for law in subject.check([1.0, 2.0, 8.0], merge, str) if not law.held}
    assert broken == {"associative"}


def test_a_law_names_the_states_that_broke_it() -> None:
    states = [counters.GCounter(), counters.GCounter({"a": 1}), counters.GCounter({"b": 2})]
    laws = subject.check(states, lambda left, right: right, _canon)
    failed = [law for law in laws if not law.held]
    assert failed and "pairs" in failed[0].detail


def test_law_checks_need_two_states() -> None:
    with pytest.raises(ValueError):
        subject.check([counters.GCounter()], counters.GCounter.merge, _canon)
