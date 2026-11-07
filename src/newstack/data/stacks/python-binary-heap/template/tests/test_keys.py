from __future__ import annotations

import pytest

from {{ package_name }}.keys import (
    MAX_KEY,
    KeysError,
    describe,
    ensure_key,
)


def test_integers_pass_and_come_back() -> None:
    assert ensure_key(0) == 0
    assert ensure_key(-MAX_KEY) == -MAX_KEY
    assert ensure_key(MAX_KEY) == MAX_KEY


def test_noise_is_refused() -> None:
    for candidate in (1.5, "7", True, None, [4]):
        with pytest.raises(KeysError):
            ensure_key(candidate)


def test_oversized_is_refused() -> None:
    with pytest.raises(KeysError):
        ensure_key(MAX_KEY + 1)
    with pytest.raises(KeysError):
        ensure_key(-MAX_KEY - 1)


def test_the_display_form_is_the_number() -> None:
    assert describe(-7) == "-7"
