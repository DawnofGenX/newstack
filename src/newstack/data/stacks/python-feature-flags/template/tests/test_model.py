"""A flag refuses to be ambiguous."""

from __future__ import annotations

import pytest

from {{ package_name }} import model as subject


def test_a_flag_reports_its_cutoff_in_basis_points() -> None:
    assert subject.Flag(name="checkout", rollout=10, salt="s").cutoff == 1000


def test_a_fresh_flag_is_enabled_and_empty() -> None:
    flag = subject.Flag(name="a", salt="s")
    assert flag.enabled is True
    assert flag.rollout == 0
    assert flag.targets == frozenset()


@pytest.mark.parametrize(
    "name", ["check out", "Checkout", "1checkout", "", "checkout_redesign", "checkout!"]
)
def test_a_name_that_is_not_a_slug_is_refused(name: str) -> None:
    with pytest.raises(subject.InputError, match="not a slug"):
        subject.Flag(name=name, salt="s")


@pytest.mark.parametrize("rollout", [True, False, 1.5, "10", None])
def test_a_rollout_that_is_not_an_integer_is_refused(rollout: object) -> None:
    with pytest.raises(subject.InputError, match="integer percent"):
        subject.Flag(name="a", rollout=rollout, salt="s")


@pytest.mark.parametrize("rollout", [-1, 101])
def test_a_rollout_outside_zero_to_a_hundred_is_refused(rollout: int) -> None:
    with pytest.raises(subject.InputError, match="between 0 and 100"):
        subject.Flag(name="a", rollout=rollout, salt="s")


def test_a_flag_without_a_salt_is_refused() -> None:
    with pytest.raises(subject.InputError, match="salt is required"):
        subject.Flag(name="a", rollout=5)


def test_a_non_boolean_enabled_is_refused() -> None:
    with pytest.raises(subject.InputError, match="enabled must be true or false"):
        subject.Flag(name="a", salt="s", enabled="yes")  # type: ignore[arg-type]


def test_a_set_indexes_flags_by_name() -> None:
    flags = subject.FlagSet.of([subject.Flag(name="a", salt="s")])
    assert "a" in flags
    assert "b" not in flags
    assert flags["a"].name == "a"
    assert len(flags) == 1


def test_an_unknown_flag_lists_the_known_ones() -> None:
    flags = subject.FlagSet.of([subject.Flag(name="a", salt="s")])
    with pytest.raises(subject.InputError, match="known flags are: a"):
        flags["b"]


def test_a_duplicate_flag_is_refused() -> None:
    with pytest.raises(subject.InputError, match="duplicate flag"):
        subject.FlagSet.of(
            [subject.Flag(name="a", salt="s"), subject.Flag(name="a", salt="t")]
        )


def test_a_flag_line_is_greppable() -> None:
    line = subject.Flag(name="checkout", rollout=10, salt="s").line()
    assert line.startswith("checkout                 on   10%  salt=s")
