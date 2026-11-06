"""The command line: record, report percentiles, merge, inspect, demo, selftest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import demo as demo_module
from . import selftest as selftest_module
from .histogram import (
    DEFAULT_SIGNIFICANT_BITS,
    Histogram,
    HistogramError,
    parse_histogram,
)
from .stats import StatsError, check

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BREACH = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """Something the command line could not make sense of."""


def load_latencies(path: str) -> list[int]:
    """One latency per line, as a bare integer or as ``{"latency": n}``."""
    location = Path(path)
    if not location.exists():
        raise UsageError(f"no such file: {path}")
    values: list[int] = []
    for number, line in enumerate(location.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        if text.startswith("{"):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as error:
                raise UsageError(f"{path}: line {number} is not JSON: {error.msg}") from error
            if not isinstance(payload, dict) or "latency" not in payload:
                raise UsageError(f"{path}: line {number} needs a 'latency' field")
            value = payload["latency"]
        else:
            try:
                value = int(text)
            except ValueError as error:
                raise UsageError(f"{path}: line {number} is not a whole number") from error
        try:
            values.append(int(value))
        except (TypeError, ValueError) as error:
            raise UsageError(f"{path}: line {number} is not a whole number") from error
    if not values:
        raise UsageError(f"{path} holds no latencies, and a histogram of nothing has no answer")
    return values


def load_histogram(path: str) -> Histogram:
    location = Path(path)
    if not location.exists():
        raise UsageError(f"no such file: {path}")
    try:
        payload = json.loads(location.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise UsageError(f"{path} is not JSON: {error.msg}") from error
    return parse_histogram(payload)


def _parse_points(text: str) -> list[float]:
    points: list[float] = []
    for piece in text.split(","):
        piece = piece.strip()
        if not piece:
            continue
        try:
            points.append(float(piece))
        except ValueError as error:
            raise UsageError(f"'{piece}' is not a percentile") from error
    if not points:
        raise UsageError("--p needs at least one percentile")
    return points


def _command_record(arguments: argparse.Namespace) -> int:
    values = load_latencies(arguments.input)
    histogram = Histogram(arguments.bits)
    histogram.record_many(values)
    if arguments.out:
        Path(arguments.out).write_text(json.dumps(histogram.as_dict(), indent=2) + "\n", "utf-8")
    payload = {
        "samples": histogram.count(),
        "significant_bits": histogram.significant_bits,
        "error": histogram.error,
        "buckets": histogram.buckets_used,
        "bytes": histogram.bytes_used,
        "out": arguments.out,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK
    print(f"samples      {histogram.count()}")
    bits = histogram.significant_bits
    print(f"bits         {bits} (relative error at most {histogram.error * 100:.4f}%)")
    print(f"buckets      {histogram.buckets_used} used, {histogram.bytes_used} byte(s)")
    if arguments.out:
        print(f"written      {arguments.out}")
    return EXIT_OK


def _command_percentile(arguments: argparse.Namespace) -> int:
    values = load_latencies(arguments.input)
    histogram = Histogram(arguments.bits)
    histogram.record_many(values)
    points = tuple(_parse_points(arguments.p))
    compared = check(histogram, values, points)
    payload = {
        "samples": compared.samples,
        "promised": compared.promised,
        "worst": compared.worst,
        "held": compared.held(),
        "percentiles": [
            {
                "p": row.percentile,
                "reported": row.reported,
                "truth": row.truth,
                "relative_error": row.relative_error,
            }
            for row in compared.rows
        ],
    }
    code = EXIT_OK if compared.held() else EXIT_BREACH
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return code
    print(f"left         {len(values)} sample(s), promised {compared.promised * 100:.4f}%")
    for line in compared.lines():
        print(line)
    verdict = "within the promise" if compared.held() else "BREACH: wider than promised"
    print(f"result       {verdict}")
    return code


def _command_merge(arguments: argparse.Namespace) -> int:
    left = load_histogram(arguments.left)
    right = load_histogram(arguments.right)
    merged = left.merged(right)
    if arguments.out:
        Path(arguments.out).write_text(json.dumps(merged.as_dict(), indent=2) + "\n", "utf-8")
    payload = {
        "left": left.count(),
        "right": right.count(),
        "merged": merged.count(),
        "buckets": merged.buckets_used,
        "bytes": merged.bytes_used,
        "out": arguments.out,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK
    print(f"left         {left.count()} sample(s)")
    print(f"right        {right.count()} sample(s)")
    print(f"merged       {merged.count()} sample(s), {merged.buckets_used} bucket(s)")
    if arguments.out:
        print(f"written      {arguments.out}")
    return EXIT_OK


def _command_info(arguments: argparse.Namespace) -> int:
    histogram = load_histogram(arguments.histogram)
    payload = {
        "samples": histogram.count(),
        "exact_sum": histogram.total_sum,
        "mean": histogram.total_sum / histogram.total if histogram.total else None,
        "minimum": histogram.lowest,
        "p99": histogram.percentile(99.0) if histogram.total else None,
        "buckets": histogram.buckets_used,
        "bytes": histogram.bytes_used,
        "significant_bits": histogram.significant_bits,
        "error": histogram.error,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK
    print(f"samples      {payload['samples']}")
    print(f"minimum      {payload['minimum']}")
    print(
        f"mean         {payload['mean'] if payload['mean'] is None else round(payload['mean'], 2)}"
    )
    print(f"p99          {payload['p99']}")
    print(f"buckets      {payload['buckets']} used, {payload['bytes']} byte(s)")
    resolution = payload["significant_bits"]
    print(f"bits         {resolution} (relative error at most {payload['error'] * 100:.4f}%)")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Record latencies into bounded-error buckets and report percentiles.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    parser.set_defaults(handler=None)
    subparsers = parser.add_subparsers(dest="command")

    record = subparsers.add_parser("record", help="record a latency file into a histogram")
    record.add_argument("--input", required=True, help="one latency per line")
    record.add_argument("--out", help="where to write the histogram JSON")
    record.add_argument("--bits", type=int, default=DEFAULT_SIGNIFICANT_BITS)
    record.add_argument("--json", action="store_true")
    record.set_defaults(handler=_command_record)

    percentile = subparsers.add_parser("percentile", help="report percentiles against the truth")
    percentile.add_argument("--input", required=True)
    percentile.add_argument("--p", default="50,90,99,99.9")
    percentile.add_argument("--bits", type=int, default=DEFAULT_SIGNIFICANT_BITS)
    percentile.add_argument("--json", action="store_true")
    percentile.set_defaults(handler=_command_percentile)

    merge = subparsers.add_parser("merge", help="merge two histograms")
    merge.add_argument("--left", required=True)
    merge.add_argument("--right", required=True)
    merge.add_argument("--out")
    merge.add_argument("--json", action="store_true")
    merge.set_defaults(handler=_command_merge)

    info = subparsers.add_parser("info", help="describe a stored histogram")
    info.add_argument("--histogram", required=True)
    info.add_argument("--json", action="store_true")
    info.set_defaults(handler=_command_info)

    demo = subparsers.add_parser("demo", help="run the six stories")
    demo.set_defaults(handler=_command_demo)

    selftest = subparsers.add_parser("selftest", help="run the in-process checks")
    selftest.set_defaults(handler=_command_selftest)
    return parser


def _command_demo(arguments: argparse.Namespace) -> int:
    del arguments
    return demo_module.main()


def _command_selftest(arguments: argparse.Namespace) -> int:
    del arguments
    return selftest_module.main()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.handler is None:
        parser.print_help()
        return EXIT_UNUSABLE
    try:
        return int(arguments.handler(arguments))
    except (UsageError, HistogramError, StatsError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
