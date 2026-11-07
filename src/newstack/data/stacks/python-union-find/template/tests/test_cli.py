from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli
from {{ package_name }}.forest import UnionFind


def workload(path: object, text: str) -> str:
    location = str(path)
    with open(location, "w", encoding="utf-8") as handle:
        handle.write(text)
    return location


def test_version_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


def test_help_lists_the_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["--help"]) == 0
    listed = capsys.readouterr().out
    for command in ("build", "add", "union", "connected", "components", "count", "demo"):
        assert command in listed


def test_unknown_flag_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["--bogus"]) == 2


def test_build_lists_the_partition(tmp_path: object, capsys: pytest.CaptureFixture[str]) -> None:
    pairs = workload(tmp_path / "pairs.txt", "1 2\n3 4\n2 4\n")
    assert cli.main(["build", "--pairs", pairs]) == 0
    printed = capsys.readouterr().out
    assert "elements   4, components 1" in printed


def test_a_missing_workload_is_unusable(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["build", "--pairs", "nowhere.txt"]) == 2
    assert "no such workload" in capsys.readouterr().err


def test_add_reports_opening(
    tmp_path: object,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pairs = workload(tmp_path / "pairs.txt", "5 6\n")
    assert cli.main(["add", "--pairs", pairs, "--element", "5"]) == 1
    assert "opened     False" in capsys.readouterr().out
    assert cli.main(["add", "--pairs", pairs, "--element", "9"]) == 0


def test_union_reports_merging(
    tmp_path: object,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pairs = workload(tmp_path / "pairs.txt", "1 2\n3 4\n")
    assert cli.main(["union", "--pairs", pairs, "--first", "1", "--second", "2"]) == 1
    assert "merged     False" in capsys.readouterr().out
    assert cli.main(["union", "--pairs", pairs, "--first", "1", "--second", "3"]) == 0


def test_connected_answers_with_its_exit_code(tmp_path: object) -> None:
    pairs = workload(tmp_path / "pairs.txt", "1 2\n3 4\n")
    assert cli.main(["connected", "--pairs", pairs, "--first", "1", "--second", "2"]) == 0
    assert cli.main(["connected", "--pairs", pairs, "--first", "1", "--second", "3"]) == 1


def test_an_outsider_pair_is_unusable(tmp_path: object) -> None:
    pairs = workload(tmp_path / "pairs.txt", "1 2\n")
    assert cli.main(["connected", "--pairs", pairs, "--first", "1", "--second", "77"]) == 2


def test_components_enumerates(tmp_path: object, capsys: pytest.CaptureFixture[str]) -> None:
    pairs = workload(tmp_path / "pairs.txt", "1 2\n3 4\n")
    assert cli.main(["components", "--pairs", pairs]) == 0
    assert "components 2" in capsys.readouterr().out


def test_count_counts(tmp_path: object, capsys: pytest.CaptureFixture[str]) -> None:
    pairs = workload(tmp_path / "pairs.txt", "1 2\n")
    assert cli.main(["count", "--pairs", pairs]) == 0
    assert "components 1" in capsys.readouterr().out


def test_json_build_is_only_json(tmp_path: object, capsys: pytest.CaptureFixture[str]) -> None:
    pairs = workload(tmp_path / "pairs.txt", "1 2\n3 4\n")
    assert cli.main(["build", "--pairs", pairs, "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["elements"] == 4
    assert payload["components"] == 2


def test_demo_states_a_fixed_forest(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["demo"]) == 0
    assert "a forest of nine" in capsys.readouterr().out


def test_selftest_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out


def test_the_package_renders_the_same_forest_twice() -> None:
    first = UnionFind([1, 2, 3])
    first.union(1, 2)
    second = UnionFind([1, 2, 3])
    second.union(2, 1)
    assert first.components() == second.components()
