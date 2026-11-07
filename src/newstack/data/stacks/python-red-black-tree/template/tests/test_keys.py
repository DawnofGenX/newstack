from __future__ import annotations

import pytest

from {{ package_name }}.keys import (
    MAX_KEY,
    KeyError,
    describe_key,
    ensure_key,
)


def test_an_integer_passes_the_gate() -> None:
    assert ensure_key(0) == 0
    assert ensure_key(-13) == -13
    assert ensure_key(MAX_KEY) == MAX_KEY
    assert ensure_key(-MAX_KEY) == -MAX_KEY


def test_the_edge_refuses_the_next_key() -> None:
    with pytest.raises(KeyError):
        ensure_key(MAX_KEY + 1)
    with pytest.raises(KeyError):
        ensure_key(-MAX_KEY - 1)


def test_halves_and_bools_are_never_keys() -> None:
    for junk in (1.0, True, False, "7", None, [7]):
        with pytest.raises(KeyError):
            ensure_key(junk)


def test_the_gate_is_the_same_answer_as_the_error() -> None:
    assert issubclass(KeyError, ValueError)
    with pytest.raises(ValueError):
        ensure_key(2.5)


def test_the_description_is_the_plain_number() -> None:
    assert describe_key(13) == "13"
    assert describe_key(-13) == "-13"
    with pytest.raises(KeyError):
        describe_key(1.5)
