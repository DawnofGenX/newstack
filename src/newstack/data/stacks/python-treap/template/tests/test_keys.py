from __future__ import annotations

import pytest

from {{ package_name }}.keys import KeyValueError, describe, ensure_key


def test_the_key_comes_back_itself() -> None:
    assert ensure_key(7) == 7
    assert ensure_key("seven") == "seven"
    assert ensure_key(1.5) == 1.5


def test_int_and_float_share_one_spot_on_the_line() -> None:
    assert ensure_key(1) == ensure_key(1.0)


def test_a_rendering_exists_for_every_key() -> None:
    assert describe(7) == "7"
    assert describe(3.0) == "3"
    assert describe("towers") == "towers"


@pytest.mark.parametrize("value", [True, [1], {"a": 1}, (1,), None, object()])
def test_a_value_outside_the_order_is_refused(value: object) -> None:
    with pytest.raises(KeyValueError):
        ensure_key(value)
