"""CLI entry point."""

from __future__ import annotations

import argparse
import sys

from .thumbnailer import process_dir, thumbnail


def _parse_size(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()

    parser = argparse.ArgumentParser(prog="{{ package_name }}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    th = sub.add_parser("thumbnail")
    th.add_argument("src")
    th.add_argument("dst")
    th.add_argument("--size", default="128x128")
    th.add_argument("--quality", type=int, default=85)

    bt = sub.add_parser("batch")
    bt.add_argument("src_dir")
    bt.add_argument("dst_dir")
    bt.add_argument("--size", default="128x128")
    bt.add_argument("--quality", type=int, default=85)

    ns = parser.parse_args(args)
    if ns.cmd == "thumbnail":
        thumbnail(ns.src, ns.dst, size=ns.size, quality=ns.quality)
        print(f"thumbnail: {ns.dst}")
        return 0
    if ns.cmd == "batch":
        res = process_dir(ns.src_dir, ns.dst_dir, size=ns.size, quality=ns.quality)
        for r in res:
            print(r)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())