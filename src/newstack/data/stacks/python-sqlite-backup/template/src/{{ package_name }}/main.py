"""CLI entry point."""

from __future__ import annotations

import argparse
import sys

from .backup import BackupError, backup


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()

    parser = argparse.ArgumentParser(prog="{{ package_name }}")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup")
    b.add_argument("src")
    b.add_argument("dest_dir")
    b.add_argument("--keep", type=int, default=5)
    ns = parser.parse_args(args)

    if ns.cmd == "backup":
        try:
            out = backup(ns.src, ns.dest_dir, keep=ns.keep)
        except (BackupError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"backup: {out}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())