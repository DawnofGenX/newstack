"""A two-flag CLI, so the extension can be exercised without pytest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import count_bytes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="{{ npm_name }}")
    parser.add_argument("path", nargs="?", default="-", help="file to read, or - for stdin")
    args = parser.parse_args(argv)

    if args.path == "-":
        data = sys.stdin.buffer.read()
    else:
        try:
            data = Path(args.path).read_bytes()
        except OSError as error:
            print(f"{{ npm_name }}: {error}", file=sys.stderr)
            return 2

    lines, words, size = count_bytes(data)
    print(json.dumps({"lines": lines, "words": words, "bytes": size}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
