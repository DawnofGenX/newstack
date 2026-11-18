"""Offline self-checks for the CLI."""

from __future__ import annotations

from .cli import app


def run() -> int:
    from typer.testing import CliRunner

    runner = CliRunner()
    with runner.isolated_filesystem():
        store = "tasks.json"
        result = runner.invoke(app, ["add", "buy milk", "--file", store])
        assert result.exit_code == 0, result.output
        result = runner.invoke(app, ["list", "--file", store])
        assert result.exit_code == 0 and "buy milk" in result.output
        result = runner.invoke(app, ["done", "1", "--file", store])
        assert result.exit_code == 0, result.output
        result = runner.invoke(app, ["rm", "1", "--file", store])
        assert result.exit_code == 0, result.output
    print("selftest: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
