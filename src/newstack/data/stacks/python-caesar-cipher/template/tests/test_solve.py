from __future__ import annotations

from {{ package_name }}.solve import (
    ALPHABET,
    MAX_LENGTH,
    CipherError,
    brute_force,
    decode,
    encode,
)


def test_encode_basic() -> None:
    assert encode("abc", 3) == "def"


def test_decode_basic() -> None:
    assert decode("def", 3) == "abc"


def test_round_trip() -> None:
    assert decode(encode("Hello, World!", 7), 7) == "Hello, World!"


def test_wrap() -> None:
    assert encode("xyz", 3) == "abc"


def test_non_letters_stay() -> None:
    assert encode("a b!", 3) == "d e!"


def test_brute_force_count() -> None:
    assert len(brute_force("abc")) == ALPHABET


def test_oversized_refused() -> None:
    import pytest

    with pytest.raises(CipherError):
        encode("a" * (MAX_LENGTH + 1), 1)


def test_bad_shift_refused() -> None:
    import pytest

    with pytest.raises(CipherError):
        encode("abc", "a")
