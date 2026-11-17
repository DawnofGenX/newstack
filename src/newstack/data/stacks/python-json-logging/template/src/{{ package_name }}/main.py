"""Entry point."""

from __future__ import annotations

import sys

from .jsonlog import JsonLogger


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()
    log = JsonLogger("demo")
    log.info("hello", value=42)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())