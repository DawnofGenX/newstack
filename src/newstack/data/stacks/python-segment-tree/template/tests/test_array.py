from __future__ import annotations

from tempfile import TemporaryDirectory

from {{ package_name }}.array import (
    DEFAULT_SEED,
    ArrayValueError,
    describe,
    ensure_value,
    load_values,
    synthetic,
    write_values,
)


def test_the_value_comes_back_itself() -> None:
    assert ensure_value(7) == 7
    assert ensure_value(-3) == -3
    assert ensure_value(0) == 0


def test_a_value_renders_as_itself() -> None:
    assert describe(42) == "42"
    assert describe(-4) == "-4"


def test_a_non_number_is_refused() -> None:
    for stranger in ([1], "seven", 1.0, True, None):
        try:
            ensure_value(stranger)
        except ArrayValueError:
            continue
        raise AssertionError(f"{stranger!r} should not stand in a window")


def test_the_generator_is_deterministic() -> None:
    assert synthetic(40, seed=3) == synthetic(40, seed=3)
    assert len(synthetic(40, seed=3)) == 40
    assert DEFAULT_SEED == 7


def test_an_empty_request_is_refused() -> None:
    for call in (lambda: synthetic(0), lambda: synthetic(4, seed="three")):
        try:
            call()
        except ArrayValueError:
            continue
        raise AssertionError("a malformed request should be refused")


def test_a_written_array_reads_back() -> None:
    values = [3, -1, 4, 1, -5]
    with TemporaryDirectory() as room:
        path = f"{room}/values.txt"
        write_values(values, path)
        assert load_values(path) == values


def test_comments_and_blanks_are_skipped() -> None:
    with TemporaryDirectory() as room:
        path = f"{room}/values.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n7\n\n-2\n")
        assert load_values(path) == [7, -2]


def test_noise_is_refused() -> None:
    with TemporaryDirectory() as room:
        path = f"{room}/noise.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("one two\n")
        for call in (lambda: load_values(path), lambda: load_values(f"{room}/missing.txt")):
            try:
                call()
            except ArrayValueError:
                continue
            raise AssertionError("bad input should be refused")
