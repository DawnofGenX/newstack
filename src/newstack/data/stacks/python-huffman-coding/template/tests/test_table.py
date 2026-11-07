from __future__ import annotations

from {{ package_name }}.table import (
    CodeTable,
    TableError,
    audit,
    code_table,
    deal,
)
from {{ package_name }}.tree import (
    build_tree,
    walk_table_agreement,
)

BOOKS = (
    {"a": 10, "b": 5, "c": 2, "d": 1},
    {"a": 1, "b": 1, "c": 1, "d": 1},
    {"h": 1},
)


def _weights(text: str) -> dict[str, int]:
    return {letter: text.count(letter) for letter in set(text)}


def test_a_canonical_deal_ranks_by_length_then_letter() -> None:
    book = code_table({"a": 10, "b": 5, "c": 2, "d": 1})
    assert book.codes == {"a": "0", "b": "10", "c": "110", "d": "111"}


def test_a_lone_letter_speaks_zero() -> None:
    assert code_table({"q": 7}).codes == {"q": "0"}


def test_every_shipped_table_audits_silent() -> None:
    for weights in BOOKS:
        assert audit(code_table(weights)) == []


def test_the_deal_agrees_with_the_ladder_it_came_from() -> None:
    for weights in BOOKS:
        assert walk_table_agreement(build_tree(weights), deal(build_tree(weights)))


def test_the_mirror_reads_letters_and_words() -> None:
    book = code_table({"a": 10, "b": 5, "c": 2, "d": 1})
    assert book.bits_for("b") == "10"
    assert book.letter_for("110") == "c"
    for broken in (lambda: book.bits_for("z"), lambda: book.letter_for("1111")):
        try:
            broken()
        except TableError:
            continue
        raise AssertionError("a stranger is no word in this table")


def test_a_table_refuses_malformed_words() -> None:
    try:
        CodeTable({"a": "012"})
    except TableError:
        return
    raise AssertionError("noise is no bit string")


def test_the_deal_is_canonical_not_ladder_shape() -> None:
    # a canonical table answers through its wordlist, never by replaying
    # the ladder: same depths in, sequential words out.
    ladder = build_tree({"a": 1, "b": 1, "c": 5})
    book = deal(ladder)
    assert book.codes["c"] == "0"
