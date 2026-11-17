from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from .pipeline import run_pipeline


def _selftest() -> int:
    import polars as pl

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.parquet"
        dst = Path(tmp) / "out.parquet"
        pl.DataFrame({"value": [1, -2, 3]}).write_parquet(src)
        rows = run_pipeline(src, dst)
        out = pl.read_parquet(dst)
        assert rows == 2, rows
        assert out.columns == ["value", "doubled"], out.columns
        assert out["doubled"].to_list() == [2, 6]
    print("selftest: ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if "--selftest" in argv:
        return _selftest()
    parser = argparse.ArgumentParser(prog="polars-etl")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--input", required=True)
    run.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "run":
        n = run_pipeline(Path(args.input), Path(args.output))
        print(f"rows={n}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())