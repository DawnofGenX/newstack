"""The command line contract: exit codes and the two greppable lines."""

from __future__ import annotations

import pytest

from {{ package_name }}.cli import main


def test_cover_prints_the_coverage(capsys) -> None:
    assert main(["cover", "0", "2", "1", "3"]) == 0
    assert capsys.readouterr().out.strip() == "3"


def test_cover_accepts_a_single_pair(capsys) -> None:
    assert main(["cover", "-5", "-1"]) == 0
    assert capsys.readouterr().out.strip() == "4"


def test_cover_rejects_an_unpaired_argument(capsys) -> None:
    assert main(["cover", "0", "1", "2"]) == 2
    assert "in pairs" in capsys.readouterr().err


def test_cover_wants_at_least_one_pair(capsys) -> None:
    assert main(["cover"]) == 2
    assert "at least one" in capsys.readouterr().err


def test_a_backwards_interval_exits_two(capsys) -> None:
    assert main(["cover", "5", "2"]) == 2
    assert "ends before it starts" in capsys.readouterr().err


def test_an_unknown_command_exits_two(capsys) -> None:
    assert main(["polish"]) == 2
    captured = capsys.readouterr()
    assert "unknown command 'polish'" in captured.err
    assert "usage:" in captured.err


def test_no_command_prints_usage_to_stderr(capsys) -> None:
    assert main([]) == 2
    assert "usage:" in capsys.readouterr().err


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_help_goes_to_stdout(capsys, flag: str) -> None:
    assert main([flag]) == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.out
    assert captured.err == ""


def test_version_prints_the_name_and_version(capsys) -> None:
    from {{ package_name }} import __version__

    assert main(["--version"]) == 0
    out = capsys.readouterr().out
    assert __version__ in out
    assert out.startswith("{{ npm_name }} ")


def test_demo_prints_the_minimal_counterexample(capsys) -> None:
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "smallest input that fools a naive sum: [0, 1), [0, 1)" in out
    assert "naive sum 2   real coverage 1" in out


def test_selftest_passes(capsys) -> None:
    assert main(["--selftest"]) == 0
    assert "checks passed" in capsys.readouterr().out
