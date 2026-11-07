"""The gate: [0, 256) in, everything else refused by name."""

from __future__ import annotations

import pytest

from {{ package_name }}.universe import (
    UNIVERSE,
    UniverseError,
    describe,
    ensure_key,
    ensure_seed,
    parse_key,
)


def test_the_universe_is_256() -> None:
    assert UNIVERSE == 256


@pytest.mark.parametrize("key", [0, 1, 42, 127, 200, 255])
def test_every_key_of_the_universe_passes(key: int) -> None:
    assert ensure_key(key) == key


@pytest.mark.parametrize("candidate", [256, -1, 1000, 7.0, True, None, "7"])
def test_every_stranger_is_refused(candidate: object) -> None:
    with pytest.raises(UniverseError):
        ensure_key(candidate)


def test_digits_become_keys() -> None:
    assert parse_key("42") == 42


@pytest.mark.parametrize("text", ["x", " 7", "7.0", "-7", "", "0x7"])
def test_strange_text_is_no_key(text: str) -> None:
    with pytest.raises(UniverseError):
        parse_key(text)


def test_seeds_are_non_negative_integers() -> None:
    assert ensure_seed(0) == 0
    assert ensure_seed(2026) == 2026
    with pytest.raises(UniverseError):
        ensure_seed(-1)
    with pytest.raises(UniverseError):
        ensure_seed(True)


def test_display_pads_so_columns_hold() -> None:
    assert describe(7) == "  7"
    assert describe(255) == "255"
