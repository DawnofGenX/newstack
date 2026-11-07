from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import (
    EXIT_MISS,
    EXIT_OK,
    EXIT_UNUSABLE,
    build_parser,
    main,
)

POINTS = "points.txt"
BODY = "# fixture\n\n18,7\n20,6\n12,24\n23,5\n"


def _write(tmp_path, body: str = BODY) -> str:
    path = tmp_path / POINTS
    path.write_text(body, encoding="utf-8")
    return str(path)


def run(*argv: str) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        status = main(list(argv))
    return status, buffer.getvalue()


def test_version_and_help_exit_zero() -> None:
    assert build_parser().prog
    status, out = run("--version")
    assert status == EXIT_OK
    assert "0.1.0" in out


def test_membership_exits_on_the_answer(tmp_path) -> None:
    points = _write(tmp_path)
    assert run("has", "--points", points, "18,7")[0] == EXIT_OK
    assert run("has", "--points", points, "99,99")[0] == EXIT_MISS
    status, out = run("has", "--points", points, "18,7", "--json")
    assert status == EXIT_OK
    assert json.loads(out)["corpus"] == [[12, 24], [18, 7], [20, 6], [23, 5]]


def test_range_lists_in_order(tmp_path) -> None:
    points = _write(tmp_path)
    status, out = run("range", "--points", points, "0,0,25,25")
    assert status == EXIT_OK
    assert "inside     4 point(s)" in out
    assert "  (18, 7)" in out
    _status, out = run("range", "--points", points, "0,0,25,25", "--json")
    assert json.loads(out)["listing"] == [[12, 24], [18, 7], [20, 6], [23, 5]]
    assert run("range", "--points", points, "100,100,200,200")[0] == EXIT_MISS


def test_nearest_answers_the_argmin(tmp_path) -> None:
    points = _write(tmp_path)
    status, out = run("nearest", "--points", points, "18,7")
    assert status == EXIT_OK
    assert "nearest    (18, 7) at 0 squared" in out
    _status, out = run("nearest", "--points", points, "9,9", "--json")
    assert json.loads(out)["nearest"] == [18, 7]


def test_add_stores_and_reports(tmp_path) -> None:
    points = _write(tmp_path)
    status, out = run("add", "--points", points, "9,9")
    assert status == EXIT_OK
    assert "points     5 held, 1 added" in out
    _status, out = run("add", "--points", points, "18,7")
    assert "0 added" in out


def test_count_names_the_size(tmp_path) -> None:
    points = _write(tmp_path)
    status, out = run("count", "--points", points)
    assert status == EXIT_OK
    assert "points     4 held" in out
    assert "seated     True, splits divide" in out


def test_a_broken_input_is_unusable(tmp_path) -> None:
    points = _write(tmp_path)
    assert run("has", "--points", points, "1.5,2")[0] == EXIT_UNUSABLE
    assert run("count", "--points", str(tmp_path / "missing.txt"))[0] == \
        EXIT_UNUSABLE
    noise = tmp_path / "noise.txt"
    noise.write_text("1,2\n3,4,5\n", encoding="utf-8")
    assert run("count", "--points", str(noise))[0] == EXIT_UNUSABLE


def test_selftest_and_demo_answer_clean() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
