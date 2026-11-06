from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import (
    EXIT_NONE,
    EXIT_OK,
    EXIT_UNUSABLE,
    build_parser,
    main,
)

SPANS = "spans.txt"


def _write(tmp_path, body: str = "# fixture\n1 5\n3 9\n6 12\n") -> str:
    path = tmp_path / SPANS
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


def test_load_walks_the_fixture_in_order(tmp_path) -> None:
    status, out = run("load", "--intervals", _write(tmp_path))
    assert status == EXIT_OK
    assert "spans      3 held" in out


def test_load_json_reports_the_corpus(tmp_path) -> None:
    _status, out = run("load", "--intervals", _write(tmp_path), "--json")
    payload = json.loads(out)
    assert payload["corpus"] == ["[1..5)", "[3..9)", "[6..12)"]


def test_stab_exits_on_what_a_point_holds(tmp_path) -> None:
    spans = _write(tmp_path)
    assert run("stab", "--intervals", spans, "--point", "4")[0] == EXIT_OK
    assert run("stab", "--intervals", spans, "--point", "5")[0] == EXIT_OK
    assert run("stab", "--intervals", spans, "--point", "12")[0] == EXIT_NONE
    _status, out = run("stab", "--intervals", spans, "--point", "4", "--json")
    assert json.loads(out)["count"] == 2
    _status, out = run("stab", "--intervals", spans, "--point", "5", "--json")
    assert json.loads(out)["count"] == 1


def test_overlap_exits_on_what_a_window_touches(tmp_path) -> None:
    spans = _write(tmp_path)
    assert run("overlap", "--intervals", spans, "--low", "2", "--high", "8")[0] == EXIT_OK
    assert run("overlap", "--intervals", spans, "--low", "20", "--high", "30")[0] == EXIT_NONE
    assert run("overlap", "--intervals", spans, "--low", "9", "--high", "3")[0] == EXIT_UNUSABLE


def test_first_names_the_earliest_holder(tmp_path) -> None:
    spans = _write(tmp_path)
    status, out = run("first", "--intervals", spans, "--point", "7")
    assert status == EXIT_OK
    assert "first      [3..9)" in out
    assert run("first", "--intervals", spans, "--point", "100")[0] == EXIT_NONE


def test_a_missing_span_file_is_unusable(tmp_path) -> None:
    assert run("load", "--intervals", str(tmp_path / "gone.txt"))[0] == EXIT_UNUSABLE


def test_an_empty_span_is_unusable(tmp_path) -> None:
    assert run("load", "--intervals", _write(tmp_path, "4 4\n"))[0] == EXIT_UNUSABLE


def test_selftest_exits_zero() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
