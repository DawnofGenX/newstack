from __future__ import annotations

from {{ package_name }}.naive import (
    naive_emit,
    naive_json_roundtrip,
    naive_read,
    naive_roundtrip,
    naive_size,
)
from {{ package_name }}.tokens import (
    BackRef,
    Literal,
)


def test_the_oracle_prices_one_token_per_letter() -> None:
    assert naive_size("abra") == 4
    assert naive_size("") == 0


def test_the_oracle_emits_literals_and_reads_them_back() -> None:
    assert naive_emit("ab") == [Literal("a"), Literal("b")]
    assert naive_read(naive_emit("abra")) == "abra"
    assert naive_roundtrip("abracadabra")


def test_the_quote_replays_letters_one_step_at_a_time() -> None:
    stream = [Literal("a"), Literal("b"), BackRef(2, 4)]
    assert naive_read(stream) == "ababab"


def test_tokens_through_json_land_as_themselves() -> None:
    stream = [Literal("a"), BackRef(1, 2)]
    assert naive_json_roundtrip(stream) == stream
