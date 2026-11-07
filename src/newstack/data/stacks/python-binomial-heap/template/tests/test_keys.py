from __future__ import annotations

import pytest

from {{ package_name }}.keys import (
    KeyValueError,
    bits,
    describe,
    ensure_key,
)


def test_the_key_comes_back_itself() -> None:
    assert ensure_key(7) == 7
    assert ensure_key(0) == 0
    assert ensure_key(-77) == -77


def test_a_key_renders_as_itself() -> None:
    assert describe(42) == "42"
    assert describe(-7) == "-7"


def test_the_bits_follow_the_count() -> None:
    assert bits(0) == "0"
    assert bits(46) == "101110"
    assert bits(64) == "1000000"


@pytest.mark.parametrize("stranger", ([1], "seven", 1.0, True, None))
def test_a_non_number_is_refused(stranger: object) -> None:
    with pytest.raises(KeyValueError):
        ensure_key(stranger)
    with pytest.raises(KeyValueError):
        bits(stranger)
