from __future__ import annotations

from {{ package_name }}.naive import (
    naive_collapse,
    naive_decode,
    naive_encode,
    naive_price,
    naive_roundtrip,
)
from {{ package_name }}.rle import (
    decode,
    encode,
)
from {{ package_name }}.text import (
    TextError,
)


def test_the_oracle_prices_one_pair_per_letter() -> None:
    assert naive_price("abra") == 4
    assert naive_price("") == 0
    assert len(naive_encode("abra")) == 4


def test_the_oracle_loop_closes() -> None:
    assert naive_roundtrip("abra")
    assert naive_decode(naive_encode("abra")) == "abra"


def test_the_oracle_collapses_where_the_stepper_walks() -> None:
    for text in ("aaabbb", "abc", "mississippimississippi", ""):
        walked = "".join(pair.letter for pair in encode(text))
        assert naive_collapse(text) == walked


def test_the_oracle_read_matches_the_real_read() -> None:
    stream = [("a", 3), ("b", 2)]
    assert naive_decode(stream) == decode(stream) == "aaabb"


def test_the_oracle_refuses_loud_text() -> None:
    try:
        naive_encode("Abra")
    except TextError:
        return
    raise AssertionError("a loud text priced itself")
