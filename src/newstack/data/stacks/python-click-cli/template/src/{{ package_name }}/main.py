from __future__ import annotations

import sys

from click.testing import CliRunner

from .cli import cli


def main() -> int:
    if "--selftest" in sys.argv:
        runner = CliRunner()
        result = runner.invoke(cli, ["greet", "--name", "selftest"])
        assert result.exit_code == 0, result.output
        assert "hello selftest" in result.output
        result = runner.invoke(cli, ["count", "a b c"])
        assert result.exit_code == 0, result.output
        assert "words=3" in result.output
        print("selftest: ok")
        return 0
    return cli() or 0


if __name__ == "__main__":
    raise SystemExit(main())