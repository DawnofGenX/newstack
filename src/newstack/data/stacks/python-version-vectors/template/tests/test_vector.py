"""The comparison, the text form, and the joins that must not care about order."""

import pytest

from {{ package_name }} import vector as subject


def test_the_empty_vector_holds_nothing():
    empty = subject.VersionVector.empty()
    assert len(empty) == 0
    assert empty.total() == 0
    assert empty.text() == ""


def test_the_text_form_is_sorted_so_equal_vectors_print_alike():
    assert subject.VersionVector({"b": 1, "a": 2}).text() == "a:2,b:1"


def test_a_parsed_vector_round_trips():
    text = "a:2,b:1,c:7"
    assert subject.VersionVector.parse(text).text() == text


def test_an_empty_string_is_the_empty_vector():
    assert subject.VersionVector.parse("") == subject.VersionVector.empty()


def test_an_increment_touches_one_counter():
    before = subject.VersionVector({"a": 2, "b": 5})
    after = before.increment("a")
    assert after.get("a") == 3
    assert after.get("b") == 5
    assert before.get("a") == 2


def test_a_new_node_starts_at_one():
    assert subject.VersionVector.empty().increment("z").text() == "z:1"


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ("a:1", "a:1", "equal"),
        ("a:1", "a:2", "before"),
        ("a:2", "a:1", "after"),
        ("a:1", "b:1", "concurrent"),
        ("a:1,b:1", "a:1", "after"),
        ("", "a:1", "before"),
        ("", "", "equal"),
        ("a:1,b:2", "a:2,b:1", "concurrent"),
    ],
)
def test_every_relation(left, right, expected):
    assert (
        subject.VersionVector.parse(left).compare(subject.VersionVector.parse(right)).value
        == expected
    )


def test_concurrent_is_symmetric():
    left, right = subject.VersionVector.parse("a:3"), subject.VersionVector.parse("b:3")
    assert left.compare(right) is right.compare(left)


def test_before_and_after_are_opposites():
    small, large = subject.VersionVector.parse("a:1"), subject.VersionVector.parse("a:9")
    assert small.compare(large) is subject.Relation.BEFORE
    assert large.compare(small) is subject.Relation.AFTER


def test_two_concurrent_vectors_are_each_before_the_merge():
    left, right = subject.VersionVector.parse("a:1"), subject.VersionVector.parse("b:1")
    merged = left.merge(right)
    assert left.before(merged)
    assert right.before(merged)
    assert merged.compare(left) is subject.Relation.AFTER


def test_merge_is_idempotent_commutative_and_associative():
    a = subject.VersionVector({"a": 2, "b": 1})
    b = subject.VersionVector({"b": 3, "c": 1})
    c = subject.VersionVector({"a": 1, "c": 4})
    assert a.merge(a) == a
    assert a.merge(b) == b.merge(a)
    assert a.merge(b).merge(c) == a.merge(b.merge(c))


def test_merge_takes_the_maximum_of_each_counter():
    merged = subject.VersionVector({"a": 5, "b": 1}).merge(subject.VersionVector({"a": 2, "b": 4}))
    assert merged.text() == "a:5,b:4"


def test_merging_with_empty_changes_nothing():
    vector = subject.VersionVector({"a": 2})
    assert vector.merge(subject.VersionVector.empty()) == vector


def test_merge_all_folds_a_list():
    vectors = [subject.VersionVector({"a": 1}), subject.VersionVector({"b": 2})]
    assert subject.merge_all(vectors).text() == "a:1,b:2"
    assert subject.merge_all([]) == subject.VersionVector.empty()


def test_dominance_is_reflexive():
    vector = subject.VersionVector({"a": 1})
    assert vector.dominates(vector)


def test_an_absent_node_counts_as_zero():
    assert subject.VersionVector({"a": 1}).get("zz") == 0
    assert subject.VersionVector.empty().dominates(subject.VersionVector.empty())


def test_the_explanation_names_the_direction_of_a_concurrency():
    text = subject.explain(subject.VersionVector.parse("a:2"), subject.VersionVector.parse("b:3"))
    assert "concurrent" in text
    assert "ahead on the left" in text
    assert "ahead on the right" in text


def test_the_explanation_names_the_counter_that_moved():
    text = subject.explain(subject.VersionVector.parse("a:1"), subject.VersionVector.parse("a:4"))
    assert "before" in text
    assert "1 -> 4" in text


def test_an_equal_pair_explains_itself():
    assert "same counters" in subject.explain(
        subject.VersionVector.parse("a:1"), subject.VersionVector.parse("a:1")
    )


def test_hash_and_equality_agree():
    left = subject.VersionVector({"a": 1, "b": 2})
    right = subject.VersionVector({"b": 2, "a": 1})
    assert left == right
    assert len({left, right}) == 1


def test_a_mutation_of_the_returned_counts_does_not_reach_the_vector():
    vector = subject.VersionVector({"a": 1})
    counts = vector.counts()
    counts["a"] = 99
    assert vector.get("a") == 1


@pytest.mark.parametrize("text", ["a:1,a:2", "a", "a:-1", "a:x", ":1", "a:1,"])
def test_a_malformed_text_is_refused(text):
    with pytest.raises(subject.VectorError):
        subject.VersionVector.parse(text)


def test_a_bool_counter_is_refused():
    with pytest.raises(subject.VectorError, match="whole number"):
        subject.VersionVector({"a": True})


def test_a_colon_in_a_node_name_is_refused():
    with pytest.raises(subject.VectorError, match="cannot contain"):
        subject.VersionVector({"a:b": 1})


def test_non_text_is_refused():
    with pytest.raises(subject.VectorError, match="read from text"):
        subject.VersionVector.parse(None)  # type: ignore[arg-type]
