from __future__ import annotations

import pytest

from {{ package_name }}.keys import (
    MAX_KEY,
    KeysError,
    describe,
    ensure_key,
)


def test_signed_integers_pass_the_gate() -> None:
    for key in (0, -1, 42, -MAX_KEY, MAX_KEY):
        assert ensure_key(key) == key


def test_noise_is_refused_by_name() -> None:
    for candidate in (1.5, "7", True, None, [1]):
        with pytest.raises(KeysError):
            ensure_key(candidate)


def test_the_ceiling_is_the_ceiling() -> None:
    assert ensure_key(MAX_KEY) == MAX_KEY
    with pytest.raises(KeysError):
        ensure_key(MAX_KEY + 1)
    with pytest.raises(KeysError):
        ensure_key(-MAX_KEY - 2)


def test_the_display_form_is_the_number() -> None:
    assert describe(-7) == "-7"
