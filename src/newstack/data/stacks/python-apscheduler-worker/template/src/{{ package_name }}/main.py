"""Entry point: run N scheduler ticks."""

from __future__ import annotations

import argparse
import sys

from .worker import run_ticks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, default=5)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if args.selftest:
        from .selftest import run

        return run()
    result = run_ticks(args.ticks)
    print(f"completed {result} ticks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())