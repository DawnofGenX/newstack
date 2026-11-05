import pytest

from {{ package_name }} import fence as subject


def test_a_first_write_is_accepted() -> None:
    value = subject.FencedValue()
    value.write(1, "one")
    assert value.value == "one"
    assert value.token == 1


def test_an_older_token_is_refused() -> None:
    value = subject.FencedValue()
    value.write(2, "two")
    with pytest.raises(subject.StaleToken) as raised:
        value.write(1, "one")
    assert raised.value.token == 1
    assert raised.value.last_seen == 2


def test_the_refusal_explains_itself() -> None:
    with pytest.raises(subject.StaleToken) as raised:
        subject.FencedValue(token=5).write(3, "x")
    assert "expired and somebody else owns the resource now" in str(raised.value)


def test_one_token_may_write_many_times() -> None:
    value = subject.FencedValue()
    for number in range(3):
        value.write(1, f"v{number}")
    assert value.writes == 3
    assert value.value == "v2"


def test_a_newer_token_takes_over() -> None:
    value = subject.FencedValue()
    value.write(1, "a")
    value.write(2, "b")
    assert (value.value, value.token) == ("b", 2)


def test_an_unfenced_value_keeps_the_ghost_write() -> None:
    value = subject.UnfencedValue()
    value.write(2, "b")
    value.write(1, "a")
    assert value.value == "a"


def test_attempt_reports_both_outcomes() -> None:
    value = subject.FencedValue(token=2)
    assert subject.attempt(value, 1, "x").startswith("refused")
    assert subject.attempt(value, 3, "x").startswith("accepted")
