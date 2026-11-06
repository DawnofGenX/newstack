from __future__ import annotations

import pytest

from {{ package_name }}.keys import KeyValueError, describe, ensure_key


def test_numbers_and_strings_come_back_themselves() -> None:
    assert ensure_key(7) == 7
    assert ensure_key(1.5) == 1.5
    assert ensure_key("ladder") == "ladder"


def test_int_and_float_share_one_slot_in_the_order() -> None:
    assert ensure_key(1) == ensure_key(1.0)


@pytest.mark.parametrize("value", ([1], {1: 2}, None, True, object()))
def test_anything_else_has_no_place_in_the_order(value: object) -> None:
    with pytest.raises(KeyValueError):
        ensure_key(value)


def test_describe_renders_like_the_command_line() -> None:
    assert describe(3.0) == "3"
    assert describe("rung") == "rung"
    assert describe(-4) == "-4"
