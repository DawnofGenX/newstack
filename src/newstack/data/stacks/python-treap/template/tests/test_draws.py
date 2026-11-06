from __future__ import annotations

import pytest

from {{ package_name }}.draws import (
    DEFAULT_SEED,
    MAX_PRIORITY,
    DrawError,
    Draws,
    expected_depth,
)


def test_one_seed_hands_one_key_one_number() -> None:
    left, right = Draws(seed=9), Draws(seed=9)
    keys = ["a", 1, "c", 4]
    assert [left.shape_of(key) for key in keys] == [right.shape_of(key) for key in keys]


def test_a_different_seed_draws_a_different_number() -> None:
    assert Draws(seed=1).shape_of("same") != Draws(seed=2).shape_of("same")


def test_draws_are_wearable_priorities() -> None:
    draws = Draws(seed=3)
    for step in range(16):
        assert 0 <= draws.shape_of(step) < MAX_PRIORITY


def test_the_count_rises_with_the_asks() -> None:
    draws = Draws(seed=4)
    assert draws.count == 0
    draws.shape_of("one")
    assert draws.count == 1


def test_the_depth_promise_tracks_the_bits() -> None:
    assert expected_depth(1) == 2
    assert expected_depth(1024) == 12
    assert expected_depth(1023) == 11


@pytest.mark.parametrize("seed", ["seven", 1.5, True, None])
def test_a_seed_must_be_a_plain_number(seed: object) -> None:
    with pytest.raises(DrawError):
        Draws(seed)  # type: ignore[arg-type]


@pytest.mark.parametrize("size", [0, -1, 2.5, True])
def test_sizes_that_stand_no_tree_are_refused(size: object) -> None:
    with pytest.raises(DrawError):
        expected_depth(size)  # type: ignore[arg-type]


def test_the_default_seed_is_a_number() -> None:
    assert isinstance(DEFAULT_SEED, int)
    assert Draws().seed == DEFAULT_SEED
