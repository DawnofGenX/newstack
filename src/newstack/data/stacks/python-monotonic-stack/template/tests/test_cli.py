from __future__ import annotations

from {{ package_name }}.cli import main

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def test_greater_runs() -> None:
    assert main(["greater", "2", "1", "3"]) == EXIT_OK


def test_greater_json() -> None:
    assert main(["greater", "--json", "2", "1", "3"]) == EXIT_OK


def test_smaller_runs() -> None:
    assert main(["smaller", "2", "1", "3"]) == EXIT_OK


def test_previous_runs() -> None:
    assert main(["previous", "2", "1", "3"]) == EXIT_OK


def test_audit_runs() -> None:
    assert main(["audit", "2", "1", "3"]) == EXIT_OK


def test_demo_runs() -> None:
    assert main(["demo"]) == EXIT_OK


def test_selftest_runs() -> None:
    assert main(["selftest"]) == EXIT_OK


def test_oversized_exits_two() -> None:
    assert main(["greater", *map(str, range(65))]) == EXIT_UNUSABLE


def test_non_integer_exits_two() -> None:
    assert main(["greater", "a"]) == EXIT_UNUSABLE


def test_version_exits_zero() -> None:
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
