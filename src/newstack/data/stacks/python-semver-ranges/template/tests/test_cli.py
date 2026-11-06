"""The command line: the exit codes the README promises."""

from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


def fixtures() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures"


def test_satisfy_exits_zero_when_it_matches(capsys):
    code = subject.main(["satisfy", "1.4.2", "--range", "~1.4 || ^2.0"])
    assert code == 0
    assert "satisfies" in capsys.readouterr().out


def test_satisfy_exits_one_when_it_does_not(capsys):
    code = subject.main(["satisfy", "2.0.0", "--range", "~1.4"])
    assert code == 1
    out = capsys.readouterr().out
    assert "does not satisfy" in out
    assert "upper bound" in out


def test_satisfy_writes_json_when_asked(capsys):
    code = subject.main(["satisfy", "1.4.2", "--range", "~1.4", "--json"])
    assert code == 0
    out = capsys.readouterr().out
    assert '"satisfies": true' in out


def test_an_unreadable_version_exits_two(capsys):
    code = subject.main(["satisfy", "1.2", "--range", "*"])
    assert code == 2
    assert "not a version" in capsys.readouterr().err


def test_an_unreadable_range_exits_two(capsys):
    code = subject.main(["satisfy", "1.2.3", "--range", "1.2 || "])
    assert code == 2
    assert "empty arm" in capsys.readouterr().err


def test_parse_prints_every_arm(capsys):
    code = subject.main(["parse", "~1.4 || ^2.0"])
    assert code == 0
    out = capsys.readouterr().out
    assert "arms       2" in out
    assert "1. [1.4.0, 1.5.0)" in out
    assert "2. [2.0.0, 3.0.0)" in out


def test_intersect_prints_the_overlap(capsys):
    code = subject.main(["intersect", "^1.2.3", ">=1.4.0 <1.5.0"])
    assert code == 0
    assert "[1.4.0, 1.5.0)" in capsys.readouterr().out


def test_intersect_exits_one_when_empty(capsys):
    code = subject.main(["intersect", "^1.0", "^2.0"])
    assert code == 1
    assert "empty" in capsys.readouterr().out


def test_sort_orders_the_fixture(capsys):
    code = subject.main(["sort", "--input", str(fixtures() / "versions.txt")])
    assert code == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if line]
    assert lines[0] == "0.9.9"
    assert lines[-1] == "2.0.0"


def test_sort_refuses_a_missing_file(capsys):
    code = subject.main(["sort", "--input", "/nonexistent/versions.txt"])
    assert code == 2
    assert "no such file" in capsys.readouterr().err


def test_sort_refuses_a_bad_line(tmp_path, capsys):
    path = tmp_path / "versions.txt"
    path.write_text("1.2.3\nnope\n", encoding="utf-8")
    code = subject.main(["sort", "--input", str(path)])
    assert code == 2
    assert "line 2" in capsys.readouterr().err


def test_sort_refuses_an_empty_file(tmp_path, capsys):
    path = tmp_path / "versions.txt"
    path.write_text("\n", encoding="utf-8")
    code = subject.main(["sort", "--input", str(path)])
    assert code == 2
    assert "no versions" in capsys.readouterr().err


def test_the_parser_routes_each_command():
    parser = subject.build_parser()
    assert parser.parse_args(["parse", "^1.0"]).handler is subject._command_parse
    assert parser.parse_args(["demo"]).handler is subject._command_demo
    assert parser.parse_args(["selftest"]).handler is subject._command_selftest


@pytest.mark.parametrize("argv", [["satisfy", "1.2.3", "--range", "*"], ["parse", "*"]])
def test_a_command_that_works_returns_zero(argv):
    assert subject.main(argv) == 0
