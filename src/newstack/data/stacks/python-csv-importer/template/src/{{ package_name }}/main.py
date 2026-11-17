"""Entry point: `--selftest` for offline checks, otherwise the importer CLI."""

from __future__ import annotations

import sys

from .importer import main as cli_main
from .selftest import run as selftest_run


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest_run()
    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())