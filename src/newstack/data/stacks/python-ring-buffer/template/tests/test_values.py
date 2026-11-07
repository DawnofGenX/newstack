from __future__ import annotations

import pytest

from {{ package_name }}.values import (
    MAX_VALUE,
    ValuesError,
    describe,
    ensure_value,
)


def test_integers_come_back_themselves() -> None:
    assert ensure_value(0) == 0
    assert ensure_value(-42) == -42
    assert ensure_value(MAX_VALUE) == MAX_VALUE


def test_noise_is_refused_by_name() -> None:
    with pytest.raises(ValuesError):
        ensure_value(1.5)
    with pytest.raises(ValuesError):
        ensure_value("7")
    with pytest.raises(ValuesError):
        ensure_value(True)
    with pytest.raises(ValuesError):
        ensure_value(MAX_VALUE + 1)


def test_the_display_form_is_the_plain_number() -> None:
    assert describe(-7) == "-7"
