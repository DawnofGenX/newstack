"""Entry point: `--selftest` runs offline checks."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()
    print("use alembic upgrade head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())