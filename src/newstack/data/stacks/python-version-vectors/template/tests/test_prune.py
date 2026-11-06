"""Compaction: exact above the floor, and what happens below it."""

import pytest

from {{ package_name }} import prune as subject
from {{ package_name }} import vector


def vectors(texts):
    return [vector.VersionVector.parse(text) for text in texts]


def test_the_floor_is_the_pointwise_minimum():
    floor = subject.floor_of(vectors(["a:4,b:2", "a:3,b:6", "a:5,b:2"]))
    assert floor.text() == "a:3,b:2"


def test_the_floor_of_one_vector_is_that_vector():
    assert subject.floor_of(vectors(["a:2,b:1"])).text() == "a:2,b:1"


def test_a_vector_above_the_floor_dominates_it():
    floor = vector.VersionVector.parse("a:3,b:2")
    assert subject.dominates_floor(vector.VersionVector.parse("a:4,b:2"), floor)
    assert not subject.dominates_floor(vector.VersionVector.parse("a:2,b:2"), floor)


def test_compaction_drops_the_entries_at_the_floor_and_keeps_the_rest():
    floor = vector.VersionVector.parse("a:3,b:2")
    assert subject.compact(vector.VersionVector.parse("a:4,b:2"), floor).text() == "a:4"


def test_compaction_never_lowers_a_counter():
    floor = vector.VersionVector.parse("a:1")
    squeezed = subject.compact(vector.VersionVector.parse("a:5,b:2"), floor)
    assert squeezed.get("a") == 5
    assert squeezed.get("b") == 2


def test_compacting_the_floor_itself_leaves_nothing():
    floor = vector.VersionVector.parse("a:3,b:2")
    assert subject.compact(floor, floor).text() == ""


def test_no_verdict_changes_above_the_floor():
    above = vectors(["a:3,b:2,c:1", "a:4,b:2,c:1", "a:4,b:5,c:1", "a:5,b:5,c:1"])
    measured = subject.measure(above, vector.VersionVector.parse("a:3,b:2,c:1"))
    assert measured.changed_above == 0
    assert measured.above == 6
    assert measured.below == 0
    assert measured.held()


def test_a_verdict_changes_below_the_floor():
    mix = vectors(["a:3,b:2,c:1", "a:4,b:2,c:1", "a:4,b:5,c:1", "a:0,b:1,c:1"])
    measured = subject.measure(mix, vector.VersionVector.parse("a:3,b:2,c:1"))
    assert measured.changed_below > 0
    assert measured.examples_below
    assert measured.held()


def test_the_example_lines_name_both_verdicts():
    mix = vectors(["a:3,b:2,c:1", "a:0,b:1,c:1"])
    measured = subject.measure(mix, vector.VersionVector.parse("a:3,b:2,c:1"))
    assert "became" in measured.examples_below[0]


def test_the_pair_counts_add_up():
    mix = vectors(["a:3,b:2,c:1", "a:4,b:2,c:1", "a:0,b:1,c:1"])
    measured = subject.measure(mix, vector.VersionVector.parse("a:3,b:2,c:1"))
    assert measured.pairs == 3
    assert measured.above + measured.below == measured.pairs


def test_above_the_floor_a_verdict_is_unchanged():
    floor = vector.VersionVector.parse("a:3")
    before, after = subject.compacted_relation(
        vector.VersionVector.parse("a:4,b:1"), vector.VersionVector.parse("a:4,b:2"), floor
    )
    assert before is vector.Relation.BEFORE
    assert after is vector.Relation.BEFORE


def test_below_the_floor_two_states_can_collapse_into_one():
    floor = vector.VersionVector.parse("a:2")
    before, after = subject.compacted_relation(
        vector.VersionVector.parse("a:1,b:1"), vector.VersionVector.parse("a:2,b:1"), floor
    )
    assert before is vector.Relation.BEFORE
    assert after is vector.Relation.EQUAL


def test_an_empty_floor_is_refused():
    with pytest.raises(subject.PruneError, match="at least one vector"):
        subject.floor_of([])


def test_an_empty_measurement_is_refused():
    with pytest.raises(subject.PruneError):
        subject.measure([], vector.VersionVector.empty())


def test_the_lines_report_the_claim():
    measured = subject.measure(
        vectors(["a:3,b:2", "a:4,b:2"]), vector.VersionVector.parse("a:3,b:2")
    )
    joined = "\n".join(measured.lines())
    assert "sound above  yes" in joined
    assert "pairs 1" in joined
