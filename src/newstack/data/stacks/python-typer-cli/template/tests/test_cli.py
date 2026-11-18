from pathlib import Path

from typer.testing import CliRunner

from {{ package_name }}.cli import app


def test_add_list_done_rm(tmp_path: Path) -> None:
    runner = CliRunner()
    store = tmp_path / "tasks.json"
    result = runner.invoke(app, ["add", "buy milk", "--file", str(store)])
    assert result.exit_code == 0
    assert "added 1" in result.output

    result = runner.invoke(app, ["list", "--file", str(store)])
    assert result.exit_code == 0
    assert "buy milk" in result.output

    result = runner.invoke(app, ["done", "1", "--file", str(store)])
    assert result.exit_code == 0

    result = runner.invoke(app, ["rm", "1", "--file", str(store)])
    assert result.exit_code == 0

    result = runner.invoke(app, ["list", "--file", str(store)])
    assert result.exit_code == 0
    assert "no tasks" in result.output


def test_remove_missing_fails(tmp_path: Path) -> None:
    runner = CliRunner()
    store = tmp_path / "tasks.json"
    result = runner.invoke(app, ["rm", "99", "--file", str(store)])
    assert result.exit_code != 0
