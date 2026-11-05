from {{ package_name }} import audit as subject


def test_moved_lists_changed_keys_in_order() -> None:
    changes = subject.moved({"b": "x", "a": "x"}, {"b": "y", "a": "x"})
    assert [change.key for change in changes] == ["b"]
    assert changes[0].before == "x"
    assert changes[0].after == "y"


def test_moved_is_empty_for_identical_maps() -> None:
    assert subject.moved({"a": "x"}, {"a": "x"}) == []


def test_moved_refuses_different_key_sets() -> None:
    try:
        subject.moved({"a": "x"}, {"b": "x"})
    except subject.AuditError as error:
        assert "different keys" in str(error)
    else:
        raise AssertionError("maps with different keys were compared")


def test_only_from_names_the_source_node() -> None:
    changes = subject.moved({"a": "gone", "b": "kept"}, {"a": "here", "b": "kept"})
    assert subject.only_from(changes, "gone")
    assert not subject.only_from(changes, "kept")


def test_percentage_of_nothing_is_zero() -> None:
    assert subject.percentage(0, 0) == 0.0


def test_summary_reports_count_and_percentage() -> None:
    text = subject.summary({"a": "x", "b": "x"}, {"a": "y", "b": "x"})
    assert "1 of 2" in text
    assert "50.0%" in text


def test_mod_map_uses_the_slot_count() -> None:
    mapping = subject.mod_map([f"k{n}" for n in range(50)], ["a", "b"])
    assert set(mapping.values()) == {"a", "b"}


def test_mod_map_needs_nodes() -> None:
    try:
        subject.mod_map(["a"], [])
    except subject.AuditError as error:
        assert "no nodes" in str(error)
    else:
        raise AssertionError("an empty node list was accepted")


def test_histogram_is_sorted() -> None:
    assert list(subject.histogram({"a": "y", "b": "x", "c": "x"})) == ["x", "y"]
