from __future__ import annotations

import pytest

from {{ package_name }} import pointer as subject


def test_the_two_escapes_are_enough() -> None:
    assert subject.parse("/a~1b/m~0n") == ("a/b", "m~n")


def test_escaping_is_reversible() -> None:
    parts = ("a/b", "m~n", "plain")
    assert subject.parse(subject.render(parts)) == parts


def test_the_root_is_an_empty_tuple() -> None:
    assert subject.parse("") == ()


def test_an_empty_segment_is_a_real_key() -> None:
    assert subject.parse("/a//b") == ("a", "", "b")


def test_an_undefined_escape_is_refused() -> None:
    with pytest.raises(subject.PointerError, match="only ~0 and ~1"):
        subject.parse("/a~2b")


def test_a_pointer_must_start_with_a_slash() -> None:
    with pytest.raises(subject.PointerError, match="starts with"):
        subject.parse("a/b")


def test_an_object_key_wins_over_an_index() -> None:
    assert subject.resolve({"0": "key"}, "/0") == "key"


def test_a_list_index_is_read_as_a_number() -> None:
    assert subject.resolve(["a", "b"], "/1") == "b"


def test_a_missing_key_names_the_key() -> None:
    with pytest.raises(subject.PointerError, match="no key 'b'"):
        subject.resolve({"a": {"b": 1}}, "/b/b")


def test_the_placeholder_is_not_a_readable_index() -> None:
    with pytest.raises(subject.PointerError, match="position after the last"):
        subject.resolve(["a"], "/-")


def test_a_leading_zero_is_refused() -> None:
    with pytest.raises(subject.PointerError, match="leading zero"):
        subject.index_of("01", 5)


def test_an_index_past_the_end_is_refused() -> None:
    with pytest.raises(subject.PointerError, match="past the end"):
        subject.index_of("3", 2)


def test_a_scalar_cannot_be_walked_into() -> None:
    with pytest.raises(subject.PointerError, match="no children"):
        subject.resolve({"a": 1}, "/a/b")
