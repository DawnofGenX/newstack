from __future__ import annotations

from {{ package_name }}.tokens import (
    MAX_MATCH,
    MAX_WINDOW,
    BackRef,
    Literal,
    TokenError,
    tokens_from_json,
    tokens_to_json,
)


def test_a_literal_carries_a_quiet_letter() -> None:
    assert Literal("a").letter == "a"
    try:
        Literal("A")
    except TokenError:
        return
    raise AssertionError("uppercase passed as a letter")


def test_a_backref_keeps_its_bounds() -> None:
    assert BackRef(4, 9).offset == 4
    for offset, length in ((0, 2), (2, 1), (MAX_WINDOW + 1, 2), (2, MAX_MATCH + 1)):
        try:
            BackRef(offset, length)
        except TokenError:
            continue
        raise AssertionError(f"({offset}, {length}) passed as a quote")


def test_a_stream_survives_its_json_face() -> None:
    stream = [Literal("a"), BackRef(1, 2), Literal("b")]
    assert tokens_from_json(tokens_to_json(stream)) == stream


def test_noise_is_no_stream() -> None:
    for noise in ('[["b", 2]]', "noise", '[["c", 1, 2]]', "{}"):
        try:
            tokens_from_json(noise)
        except TokenError:
            continue
        raise AssertionError(f"{noise!r} parsed as a stream")
