from __future__ import annotations

import pytest

from {{ package_name }} import hashing as subject


def test_hash_is_stable_across_processes() -> None:
    # Baked value: hash() is salted per interpreter, blake2b is not.
    assert subject.hash64("alpha") == 5982700193828047002
    assert subject.hash64("alpha") == subject.hash64("alpha")


def test_hash_is_64_bit() -> None:
    for text in ("", "a", "user:1", "x" * 500):
        assert 0 <= subject.hash64(text) < (1 << 64)


def test_neighbouring_items_do_not_collide() -> None:
    values = {subject.hash64(f"user:{number}") for number in range(2000)}
    assert len(values) == 2000


def test_a_non_string_is_refused() -> None:
    with pytest.raises(TypeError, match="expects a string"):
        subject.hash64(7)


def test_the_biased_hash_keeps_zeroes_in_its_low_bits() -> None:
    for number in range(50):
        assert subject.hash64_biased(str(number)) & 0xFFFFFFFF == 0
