import pytest

from {{ package_name }} import orset as subject


def test_an_add_shows_up() -> None:
    assert subject.ORSet().add("x", "a").contains("x")


def test_a_remove_of_an_observed_tag_removes_it() -> None:
    assert not subject.ORSet().add("x", "a").remove("x").contains("x")


def test_removing_an_unknown_element_changes_nothing() -> None:
    assert subject.ORSet().add("x", "a").remove("y").elements() == {"x"}


def test_a_concurrent_add_survives_the_remove() -> None:
    left = subject.ORSet().add("x", "a").remove("x")
    right = subject.ORSet().add("x", "b")
    merged = left.merge(right)
    assert merged.contains("x")
    assert merged.tags_for("x") == {("b", 1)}


def test_a_remove_that_saw_every_tag_wins() -> None:
    left = subject.ORSet().add("x", "a").remove("x")
    right = subject.ORSet().add("x", "b")
    assert not left.merge(right).remove("x").contains("x")


def test_merge_unions_the_tags() -> None:
    left = subject.ORSet().add("x", "a")
    right = subject.ORSet().add("x", "b")
    assert left.merge(right).tags_for("x") == {("a", 1), ("b", 1)}


def test_tombstones_survive_a_merge() -> None:
    removed = subject.ORSet().add("x", "a").remove("x")
    stale = subject.ORSet().add("x", "a")
    assert not removed.merge(stale).contains("x")


def test_counters_merge_by_maximum() -> None:
    left = subject.ORSet().add("x", "a")
    right = subject.ORSet().add("y", "a")
    assert left.merge(right).counters == {"a": 1}


def test_an_or_set_round_trips_through_json() -> None:
    state = subject.ORSet().add("x", "a").remove("x").merge(subject.ORSet().add("x", "b"))
    assert subject.ORSet.parse(state.as_dict()) == state


def test_a_malformed_tag_is_refused() -> None:
    payload = {"type": "or-set", "entries": {"x": [[1]]}, "tombstones": [], "counters": {}}
    with pytest.raises(subject.ORSetError):
        subject.ORSet.parse(payload)


def test_an_add_without_a_node_is_refused() -> None:
    with pytest.raises(subject.ORSetError):
        subject.ORSet().add("x", "")


def test_the_plain_set_loses_the_remove() -> None:
    plain = subject.PlainSet(frozenset({"x"})).remove("x").merge(subject.PlainSet(frozenset({"x"})))
    assert plain.contains("x")
