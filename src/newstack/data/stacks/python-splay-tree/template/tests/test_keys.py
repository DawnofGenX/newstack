from __future__ import annotations

import pytest

from {{ package_name }}.keys import (
    MAX_KEY,
    KeysError,
    describe,
    ensure_key,
)


def test_a_key_comes_back_itself() -> None:
    assert ensure_key(0) == 0
    assert ensure_key(-MAX_KEY) == -MAX_KEY
    assert ensure_key(MAX_KEY) == MAX_KEY


def test_noise_is_refused() -> None:
    for candidate in (1.5, "7", True, None, MAX_KEY + 1):
        with pytest.raises(KeysError):
            ensure_key(candidate)


def test_the_display_form_is_the_number() -> None:
    assert describe(-13) == "-13"
