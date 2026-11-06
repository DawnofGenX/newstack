from __future__ import annotations

import pytest

from {{ package_name }}.keys import SkipKeyValueError, describe, ensure_key


def test_the_key_comes_back_itself() -> None:
    assert ensure_key(7) == 7
    assert ensure_key("towers") == "towers"


def test_int_and_float_share_a_slot() -> None:
    assert ensure_key(1) == ensure_key(1.0)


def test_a_list_has_no_place_in_the_order() -> None:
    with pytest.raises(SkipKeyValueError):
        ensure_key([1, 2])


def test_a_bool_is_refused_before_it_sorts_oddly() -> None:
    with pytest.raises(SkipKeyValueError):
        ensure_key(True)


def test_describe_prints_what_the_line_showed() -> None:
    assert describe("towers") == "towers"
    assert describe(3.0) == "3"
    assert describe(4) == "4"
