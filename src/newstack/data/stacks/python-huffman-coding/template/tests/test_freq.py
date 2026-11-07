from __future__ import annotations

from {{ package_name }}.freq import (
    FrequencyError,
    ensure_frequencies,
    tally,
)


def test_tally_counts_and_sorts() -> None:
    assert tally("banana") == {"a": 3, "b": 1, "n": 2}
    assert list(tally("mississippi")) == ["i", "m", "p", "s"]
    assert tally("") == {}


def test_tally_is_a_plain_count_of_what_is_there() -> None:
    counts = tally("aabbbcccc")
    assert sum(counts.values()) == 9
    assert counts == {"a": 2, "b": 3, "c": 4}


def test_a_map_must_hold_positive_letter_weights() -> None:
    assert ensure_frequencies({"b": 2, "a": 1}) == {"a": 1, "b": 2}
    for noisy in ({"a": 0}, {"a": -1}, {"A": 1}, {"ab": 1}, {"a": 1.5}, ["a"]):
        try:
            ensure_frequencies(noisy)
        except FrequencyError:
            continue
        raise AssertionError(f"{noisy!r} should not pass the gate")
