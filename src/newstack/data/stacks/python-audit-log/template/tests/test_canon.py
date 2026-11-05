"""The bytes that get hashed: sorted, tight, UTF-8, and free of floats."""

from __future__ import annotations

import pytest

from {{ package_name }} import canon as subject


def test_keys_are_sorted() -> None:
    assert subject.canonical({"z": 1, "a": 2}) == '{"a":2,"z":1}'


def test_separators_are_tight() -> None:
    assert subject.canonical({"a": [1, 2], "b": {"c": None}}) == '{"a":[1,2],"b":{"c":null}}'


def test_unicode_is_utf8_not_escaped() -> None:
    assert subject.canonical({"note": "café ünïcode"}) == '{"note":"café ünïcode"}'


def test_the_digest_ignores_insertion_order() -> None:
    assert subject.digest({"a": 1, "b": [2, 3]}) == subject.digest({"b": [2, 3], "a": 1})


def test_the_digest_is_lowercase_hex() -> None:
    value = subject.digest({"a": 1})
    assert len(value) == 64
    assert value == value.lower()
    assert set(value) <= set("0123456789abcdef")


@pytest.mark.parametrize("value", [{"ratio": 0.5}, {"rows": [1.5]}, {"deep": {"x": [0.1]}}])
def test_floats_are_refused(value: dict) -> None:
    with pytest.raises(subject.CanonError, match="is a float"):
        subject.canonical(value)


def test_a_float_message_explains_the_runtime_disagreement() -> None:
    with pytest.raises(subject.CanonError, match="JavaScript"):
        subject.canonical({"a": 1.0})


@pytest.mark.parametrize("value", [{"a": {1, 2}}, {"a": object()}, {1: "one"}, {"a": b"x"}])
def test_values_json_cannot_represent_are_refused(value: dict) -> None:
    with pytest.raises(subject.CanonError):
        subject.canonical(value)


def test_nesting_is_validated_all_the_way_down() -> None:
    with pytest.raises(subject.CanonError, match=r"\$\.rows\[1\]\.ratio"):
        subject.canonical({"rows": [{"ratio": 1}, {"ratio": 2.5}]})
