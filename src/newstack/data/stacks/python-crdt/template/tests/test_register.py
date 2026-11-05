import pytest

from {{ package_name }} import register as subject


def test_an_empty_register_says_so() -> None:
    assert subject.LWWRegister().is_empty


def test_the_first_write_applies() -> None:
    register, write = subject.LWWRegister().assign("red", 1_000, "a")
    assert register.value == "red"
    assert write.applied and write.previous is None


def test_a_newer_write_wins_and_reports_what_it_replaced() -> None:
    register, _ = subject.LWWRegister().assign("red", 1_000, "a")
    register, write = register.assign("green", 1_001, "a")
    assert register.value == "green"
    assert write.previous == subject.Stamp(1_000, "a")


def test_an_older_write_is_ignored() -> None:
    register, _ = subject.LWWRegister().assign("red", 1_000, "a")
    register, write = register.assign("blue", 999, "z")
    assert register.value == "red"
    assert not write.applied
    assert "newer" in write.line(subject.Stamp(999, "z"))


def test_the_node_breaks_a_tie() -> None:
    left, _ = subject.LWWRegister().assign("red", 1_000, "a")
    right, _ = subject.LWWRegister().assign("blue", 1_000, "b")
    assert left.merge(right).value == "blue"


def test_merge_keeps_the_newest_stamp() -> None:
    old = subject.LWWRegister("red", subject.Stamp(1_000, "a"))
    new = subject.LWWRegister("green", subject.Stamp(2_000, "b"))
    assert old.merge(new) == new


def test_two_values_under_one_stamp_are_refused() -> None:
    left = subject.LWWRegister("red", subject.Stamp(1_000, "a"))
    right = subject.LWWRegister("blue", subject.Stamp(1_000, "a"))
    with pytest.raises(subject.RegisterError):
        left.merge(right)


def test_a_register_round_trips_through_json() -> None:
    register = subject.LWWRegister("red", subject.Stamp(1_000, "a"))
    assert subject.LWWRegister.parse(register.as_dict()) == register


def test_a_value_without_a_stamp_cannot_be_built() -> None:
    with pytest.raises(subject.RegisterError):
        subject.LWWRegister("red", None)


def test_a_value_without_a_stamp_cannot_be_parsed() -> None:
    payload = {"type": "lww-register", "value": "red", "stamp": None}
    with pytest.raises(subject.RegisterError):
        subject.LWWRegister.parse(payload)
