from __future__ import annotations

from {{ package_name }}.naive import (
    naive_collapse,
    naive_price,
)
from {{ package_name }}.pairs import (
    MAX_RUN,
    Pair,
    walk_runs,
)
from {{ package_name }}.rle import (
    RunError,
    audit,
    decode,
    encode,
)
from {{ package_name }}.text import (
    TextError,
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
REPEATS = ("abracadabbra" * 3, "baanana" * 6, "a" * 48, "mississippi" * 4)


def test_the_loop_closes_on_every_shipped_text() -> None:
    for text in TEXTS:
        assert decode(encode(text)) == text


def test_encode_answers_the_stepper() -> None:
    for text in TEXTS:
        assert encode(text) == list(walk_runs(text))


def test_the_collapsed_view_is_the_walked_letters() -> None:
    for text in TEXTS:
        walked = "".join(pair.letter for pair in walk_runs(text))
        assert walked == naive_collapse(text)


def test_a_repeat_costs_fewer_pairs_than_letters() -> None:
    for text in REPEATS:
        assert len(encode(text)) < len(text)


def test_no_text_pays_more_than_the_naive_price() -> None:
    for text in TEXTS:
        assert len(encode(text)) <= naive_price(text)


def test_a_pair_stream_replays_letter_by_letter() -> None:
    assert decode([Pair("a", 3), Pair("b", 1)]) == "aaab"


def test_a_broken_stream_is_refused() -> None:
    try:
        decode([("a", 0)])
    except RunError:
        return
    raise AssertionError("a broken stream answered")


def test_a_loud_text_is_refused() -> None:
    try:
        encode("ABRA")
    except TextError:
        return
    raise AssertionError("a loud text was encoded")


def test_the_audit_of_honest_streams_is_silent() -> None:
    for text in TEXTS:
        assert audit(encode(text)) == []
    assert audit([]) == []


def test_the_ceiling_is_the_documented_one() -> None:
    assert MAX_RUN == 255
    run = "c" * (MAX_RUN * 2 + 5)
    pairs = encode(run)
    assert sum(pair.count for pair in pairs) == len(run)
    assert decode(pairs) == run
