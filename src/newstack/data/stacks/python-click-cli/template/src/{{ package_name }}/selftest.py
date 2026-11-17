"""Offline self-checks for the CLI."""

from __future__ import annotations

from click.testing import CliRunner

from .cli import cli


def run() -> int:
    runner = CliRunner()
    result = runner.invoke(cli, ["greet", "--name", "selftest"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(cli, ["count", "a b c"])
    assert result.exit_code == 0, result.output
    print("selftest: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())