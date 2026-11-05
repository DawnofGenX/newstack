import pytest

from {{ package_name }} import counter as subject


def test_a_grow_only_counter_sums_its_nodes() -> None:
    assert subject.GCounter().increment("a", 3).increment("b", 2).value() == 5


def test_merge_takes_the_highest_count_per_node() -> None:
    merged = subject.GCounter({"a": 3, "b": 1}).merge(subject.GCounter({"b": 4, "c": 2}))
    assert merged.counts == {"a": 3, "b": 4, "c": 2}


def test_merge_is_commutative() -> None:
    left = subject.GCounter({"a": 3})
    right = subject.GCounter({"b": 5})
    assert left.merge(right) == right.merge(left)


def test_a_counter_round_trips_through_json() -> None:
    counter = subject.GCounter({"a": 3})
    assert subject.GCounter.parse(counter.as_dict()) == counter


@pytest.mark.parametrize(
    "payload",
    [{"a": -1}, {"a": True}, {"a": 1.5}, {"": 1}],
)
def test_a_stored_count_that_cannot_be_real_is_refused(payload: dict) -> None:
    with pytest.raises(subject.CounterError):
        subject.GCounter(payload)


def test_an_increment_must_be_positive() -> None:
    with pytest.raises(subject.CounterError):
        subject.GCounter().increment("a", 0)


def test_an_anonymous_increment_is_refused() -> None:
    with pytest.raises(subject.CounterError):
        subject.GCounter().increment("")


def test_a_state_of_another_type_is_refused() -> None:
    with pytest.raises(subject.CounterError):
        subject.GCounter.parse({"type": "or-set", "counts": {}})


def test_the_signed_trap_loses_the_later_decrement() -> None:
    older = subject.SignedTotal().apply("a", -1)
    newer = older.apply("a", -1)
    assert newer.value() == -2
    assert older.merge(newer).value() == -1


def test_the_counter_pair_keeps_both_decrements() -> None:
    left = subject.PNCounter().decrement("a", 1)
    right = subject.PNCounter().decrement("b", 1)
    assert left.merge(right).value() == -2


def test_the_halves_merge_independently() -> None:
    left = subject.PNCounter().increment("a", 5)
    right = subject.PNCounter().decrement("b", 2)
    assert left.merge(right).value() == 3


def test_a_counter_pair_round_trips_through_json() -> None:
    counter = subject.PNCounter().increment("a", 2).decrement("b", 1)
    assert subject.PNCounter.parse(counter.as_dict()) == counter


def test_a_negative_stored_half_is_refused() -> None:
    payload = {"type": "pn-counter", "positive": {"a": -1}, "negative": {}}
    with pytest.raises(subject.CounterError):
        subject.PNCounter.parse(payload)
