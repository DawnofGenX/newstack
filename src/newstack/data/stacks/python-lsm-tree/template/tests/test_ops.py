from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }}.ops import (
    DELETE,
    GET,
    PUT,
    OpsError,
    load_ops,
    parse_line,
    replay_dict,
    workload,
)


def test_a_workload_is_the_same_stream_twice() -> None:
    assert workload(40, seed=9) == workload(40, seed=9)
    assert workload(40, seed=9) != workload(40, seed=10)


def test_a_workload_counts_one_op_or_more() -> None:
    with pytest.raises(OpsError):
        workload(0, seed=1)
    with pytest.raises(OpsError):
        workload(4, 1, low=5, high=5)


def test_parse_line_reads_each_op() -> None:
    assert parse_line("put 7 text here", 1) == (PUT, 7, "text here")
    assert parse_line("del -3", 1) == (DELETE, -3, None)
    assert parse_line("get 4", 1) == (GET, 4, None)


def test_parse_line_names_what_it_cannot_read() -> None:
    with pytest.raises(OpsError):
        parse_line("frobnicate 1", 1)
    with pytest.raises(OpsError):
        parse_line("put 7", 1)
    with pytest.raises(OpsError):
        parse_line("get 7 extra", 1)
    with pytest.raises(OpsError):
        parse_line("put x text", 1)


def test_load_skips_blanks_and_comments(tmp_path: Path) -> None:
    path = tmp_path / "ops.txt"
    path.write_text("# a comment\nput 3 text here\n\nget 3\ndel 3\n", encoding="utf-8")
    assert len(load_ops(path)) == 3


def test_a_file_of_comments_replays_nothing(tmp_path: Path) -> None:
    path = tmp_path / "none.txt"
    path.write_text("# nothing but a comment\n", encoding="utf-8")
    with pytest.raises(OpsError):
        load_ops(path)


def test_the_dict_answers_the_stream_the_table_will_answer() -> None:
    stream = [
        (PUT, 1, "a"),
        (PUT, 2, "b"),
        (DELETE, 1, None),
        (PUT, 2, "c"),
        (GET, 1, None),
    ]
    assert replay_dict(stream) == {2: "c"}


def test_the_workload_mixes_writes_deletes_and_reads() -> None:
    stream = workload(200, seed=7)
    ops = {op for op, _, _ in stream}
    assert {PUT, DELETE, GET} == ops
    answers = replay_dict(stream)
    assert answers and all(isinstance(key, int) for key in answers)
