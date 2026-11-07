from __future__ import annotations

from {{ package_name }}.coder import (
    MIN_MATCH,
    CoderError,
    audit,
    compress,
    decompress,
)
from {{ package_name }}.naive import (
    naive_read,
    naive_size,
)
from {{ package_name }}.text import (
    TextError,
)
from {{ package_name }}.tokens import (
    MAX_MATCH,
    MAX_WINDOW,
    BackRef,
    Literal,
)

TEXTS = (
    "",
    "a",
    "ab",
    "abracadabra",
    "bananabananabana",
    "mississippimississippi",
    "aaaaaaaaaaaaaaaaaaaaaaaa",
    "abcabcabcabcabcabcabc",
)
REPEATS = ("abracadabra" * 3, "banana" * 6, "a" * 48, "mississippi" * 4)


def test_the_loop_closes_on_every_shipped_text() -> None:
    for text in TEXTS:
        assert decompress(compress(text)) == text


def test_every_shipped_stream_audits_silent() -> None:
    for text in TEXTS:
        assert audit(compress(text)) == []


def test_a_repeat_costs_fewer_tokens_than_letters() -> None:
    for text in REPEATS:
        assert len(compress(text)) < len(text)


def test_no_text_costs_more_than_the_naive_price() -> None:
    for text in TEXTS:
        assert len(compress(text)) <= naive_size(text)


def test_a_quote_may_ride_its_own_tail() -> None:
    stream = [Literal("a")] * 5 + [BackRef(5, 10)]
    assert decompress(stream) == "a" * 15
    assert audit(stream) == []
    assert naive_read(stream) == decompress(stream)


def test_the_empty_text_streams_empty() -> None:
    assert compress("") == []
    assert decompress([]) == ""


def test_a_quote_into_nothing_is_refused() -> None:
    try:
        decompress([BackRef(3, 2)])
    except CoderError:
        return
    raise AssertionError("a quote into nothing answered")


def test_a_loud_text_is_refused() -> None:
    try:
        compress("ABRA")
    except TextError:
        return
    raise AssertionError("a loud text was compressed")


def test_the_window_and_ceiling_are_the_documented_ones() -> None:
    assert (MAX_WINDOW, MAX_MATCH, MIN_MATCH) == (4096, 32, 2)
