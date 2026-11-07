from __future__ import annotations

import pytest

from {{ package_name }}.keys import (
    MAX_KEY,
    UNIVERSE,
    KeysError,
    describe,
    ensure_key,
)


def test_seats_pass_the_gate() -> None:
    for key in (0, 7, 200, MAX_KEY):
        assert ensure_key(key) == key


def test_noise_is_refused_by_name() -> None:
    for candidate in (1.5, "7", True, None, [1], -1, UNIVERSE):
        with pytest.raises(KeysError):
            ensure_key(candidate)


def test_the_universe_is_the_universe() -> None:
    assert UNIVERSE == MAX_KEY + 1 == 256
    with pytest.raises(KeysError):
        ensure_key(MAX_KEY + 1)


def test_the_display_form_is_the_number() -> None:
    assert describe(7) == "7"
