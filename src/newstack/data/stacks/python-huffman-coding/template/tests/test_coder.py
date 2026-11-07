from __future__ import annotations

import json

from {{ package_name }}.coder import (
    CoderError,
    decode,
    encode,
    honest,
    size_report,
)
from {{ package_name }}.corpus import stream_json
from {{ package_name }}.table import (
    CodeTable,
    audit,
    code_table,
)

TEXTS = (
    "",
    "a",
    "ab",
    "abracadabra",
    "bananabananabana",
    "mississippimississippi",
    "aaaaaaaaaaaaaaaaaaaaaaaa",
    "thequickbrownfoxjumpsoverthelazydog",
)
SKEWED = ("a" * 40, "aaaaaaaaaabbbbcc", "mississippi" * 4)


def test_the_loop_closes_on_every_shipped_text() -> None:
    for text in TEXTS:
        if not text:
            assert encode("") == ""
            continue
        book = code_table({letter: text.count(letter) for letter in set(text)})
        assert decode(encode(text, book), book) == text


def test_encode_without_a_table_pays_the_same_as_with_one() -> None:
    text = "huffmanhuffman"
    book = code_table({letter: text.count(letter) for letter in set(text)})
    assert encode(text) == encode(text, book)


def test_the_empty_text_spends_no_bits() -> None:
    assert encode("") == ""
    assert decode("", code_table({"a": 1})) == ""


def test_a_skewed_text_pays_strictly_under_eight_bits_a_letter() -> None:
    for text in SKEWED:
        letters, bits, _ = size_report(text)
        assert bits < letters * 8


def test_size_report_and_encode_share_the_ledger() -> None:
    for text in TEXTS:
        if not text:
            continue
        letters, bits, book = size_report(text)
        assert letters == len(text)
        assert bits == len(encode(text, book))
        assert audit(book) == []
        assert honest(text)


def test_a_clipped_or_noisy_stream_is_refused() -> None:
    book = code_table({"a": 1, "b": 2, "c": 3})
    for noise in ("1", "02", "111"):
        try:
            decode(noise, book)
        except CoderError:
            continue
        raise AssertionError(f"{noise!r} should decode nowhere")


def test_the_loop_holds_through_the_json_wire() -> None:
    for text in TEXTS:
        if not text:
            continue
        wire = json.loads(stream_json(text))
        shipped = CodeTable(dict(wire["codes"]))
        assert audit(shipped) == []
        assert decode(wire["bits"], shipped) == text
