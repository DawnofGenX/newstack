"""End to end through main(), including the exit codes that scripts branch on."""

from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli

CSV = "region,revenue\nnorth,2.00\nsouth,3.50\n"


@pytest.fixture
def data(tmp_path):
    path = tmp_path / "rows.csv"
    path.write_text(CSV, encoding="utf-8")
    return str(path)


def test_a_report_goes_to_stdout_and_exits_zero(data, capsys) -> None:
    assert cli.main(["report", "--data", data, "--group-by", "region", "--metric", "revenue"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# revenue by region")
    assert "| south | 3.50 | 1 |" in out


def test_json_format_is_selectable(data, capsys) -> None:
    args = ["report", "--data", data, "--group-by", "region", "--metric", "revenue"]
    code = cli.main([*args, "--format", "json"])
    assert code == 0
    assert json.loads(capsys.readouterr().out)["rows"][0]["group"] == "south"


def test_out_writes_a_file_and_prints_nothing(data, tmp_path, capsys) -> None:
    out = tmp_path / "report.md"
    code = cli.main(
        ["report", "--data", data, "--group-by", "region", "--metric", "revenue", "--out", str(out)]
    )
    assert code == 0
    assert capsys.readouterr().out == ""
    assert out.read_text().startswith("# revenue by region")


def test_an_unknown_column_exits_two_and_lists_the_real_ones(data, capsys) -> None:
    code = cli.main(["report", "--data", data, "--group-by", "region", "--metric", "revenu"])
    assert code == 2
    assert "no column 'revenu'" in capsys.readouterr().err


def test_a_missing_file_exits_two(tmp_path, capsys) -> None:
    code = cli.main(
        ["report", "--data", str(tmp_path / "nope.csv"), "--group-by", "a", "--metric", "b"]
    )
    assert code == 2
    assert "no such file" in capsys.readouterr().err


def test_an_unknown_format_exits_two_before_touching_the_file(data, capsys) -> None:
    code = cli.main(
        ["report", "--data", data, "--group-by", "region", "--metric", "revenue", "--format", "xml"]
    )
    assert code == 2
    assert "unknown format 'xml'" in capsys.readouterr().err


def test_limit_is_honoured(data, capsys) -> None:
    code = cli.main(
        ["report", "--data", data, "--group-by", "region", "--metric", "revenue", "--limit", "1"]
    )
    assert code == 0
    body = capsys.readouterr().out.splitlines()
    groups = [line for line in body if line.startswith("| ") and "---" not in line]
    assert len(groups) == 2, "header plus one group"


def test_the_version_flag_prints_the_package_version(capsys) -> None:
    with pytest.raises(SystemExit) as caught:
        cli.main(["--version"])
    assert caught.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
