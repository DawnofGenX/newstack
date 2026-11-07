from __future__ import annotations

from {{ package_name }}.pairs import (
    MAX_RUN,
    Pair,
    PairsError,
    pairs_from_json,
    pairs_to_json,
    walk_runs,
)


def list_runs(text: str):
    return list(walk_runs(text))


def test_a_pair_carries_a_letter_and_a_count() -> None:
    assert Pair("a", 3).letter == "a"
    assert Pair("a", 1).count == 1


def test_pairs_refuse_loud_letters_and_bad_counts() -> None:
    for letter, count in (("A", 1), ("a", 0), ("a", -2), ("a", MAX_RUN + 1), ("a", 1.5)):
        try:
            Pair(letter, count)
        except PairsError:
            continue
        raise AssertionError(f"Pair({letter!r}, {count!r}) was accepted")


def test_the_stepper_walks_each_run_once() -> None:
    assert list_runs("") == []
    assert list_runs("a") == [Pair("a", 1)]
    assert list_runs("aaabbbcc") == [Pair("a", 3), Pair("b", 3), Pair("c", 2)]
    assert list_runs("abab") == [Pair("a", 1), Pair("b", 1), Pair("a", 1), Pair("b", 1)]


def test_a_stand_past_the_ceiling_splits_without_losing_length() -> None:
    pairs = list_runs("z" * (MAX_RUN + 40))
    assert all(pair.count <= MAX_RUN for pair in pairs)
    assert sum(pair.count for pair in pairs) == MAX_RUN + 40


def test_a_stream_survives_its_json_face() -> None:
    stream = [Pair("a", 3), Pair("b", 1)]
    assert pairs_from_json(pairs_to_json(stream)) == stream


def test_noise_is_refused_as_a_stream() -> None:
    for payload in ('[["a"]]', "noise", '{"a": 1}', '[["a", 0]]'):
        try:
            pairs_from_json(payload)
        except PairsError:
            continue
        raise AssertionError(f"{payload!r} read as a stream")
