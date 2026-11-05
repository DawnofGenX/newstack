"""Create a filter on disk, add items to it, and ask it questions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bloom import Bloom, BloomFilterError, CountingBloom, parse_filter, sized_for
from .demo import render

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_PRESENT = 0
EXIT_ABSENT = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments cannot be used as given."""


def read_filter(path: Path) -> Bloom | CountingBloom:
    if not path.exists():
        raise UsageError(f"no filter at {path}; create one with `{PROGRAM} create`")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise UsageError(f"{path} is not JSON: {error}") from None
    return parse_filter(payload)


def write_filter(path: Path, bloom: Bloom | CountingBloom) -> None:
    text = json.dumps(bloom.as_dict(), sort_keys=True, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def _rate(value: float) -> str:
    """A rate of 1e-20 is not zero, and printing it as 0.000000 would say it was."""
    return f"{value:.6f}" if value >= 1e-6 else f"{value:.2e}"


def _new(kind: str, expected: int, rate: float) -> Bloom | CountingBloom:
    sizing = sized_for(expected, rate)
    factory = CountingBloom if kind == "counting" else Bloom
    return factory(sizing.m_bits, sizing.k_hashes)


def cmd_create(args: argparse.Namespace) -> int:
    path = Path(args.filter)
    if path.exists() and not args.force:
        raise UsageError(f"{path} already exists; pass --force to replace it")
    bloom = _new(args.kind, args.expected, args.rate)
    write_filter(path, bloom)
    print(f"created     {path}")
    print(f"bits        {bloom.m_bits}")
    print(f"hashes      {bloom.k_hashes}")
    print(f"kind        {bloom.type_name}")
    return EXIT_PRESENT


def cmd_add(args: argparse.Namespace) -> int:
    path = Path(args.filter)
    bloom = read_filter(path)
    for item in args.item:
        fresh = bloom.add(item)
        print(f"added       {item:<24} new bits {len(fresh)} of {bloom.k_hashes}")
    write_filter(path, bloom)
    print(f"fill        {bloom.fill():.4f} of {bloom.m_bits} bits")
    return EXIT_PRESENT


def cmd_check(args: argparse.Namespace) -> int:
    bloom = read_filter(Path(args.filter))
    present = bloom.might_contain(args.item)
    if args.json:
        print(json.dumps({"item": args.item, "present": present}, sort_keys=True))
    elif present:
        print(f"present     {args.item} (maybe: false positives are possible)")
    else:
        print(f"absent      {args.item} (definite: nothing that was added shares its bits)")
    return EXIT_PRESENT if present else EXIT_ABSENT


def cmd_info(args: argparse.Namespace) -> int:
    bloom = read_filter(Path(args.filter))
    estimate = bloom.estimate_items()
    verdict = "saturated" if bloom.is_saturated() else "healthy"
    rows = [
        ("kind", bloom.type_name),
        ("bits", str(bloom.m_bits)),
        ("hashes", str(bloom.k_hashes)),
        ("bits set", f"{bloom.bits_set()} ({bloom.fill():.4f})"),
        ("estimated items", "-" if estimate is None else f"{estimate:.1f}"),
        ("predicted rate", _rate(bloom.predict_rate())),
        ("verdict", verdict),
    ]
    if isinstance(bloom, CountingBloom):
        rows.insert(5, ("saturated counters", str(bloom.saturated_positions())))
    if args.json:
        print(
            json.dumps(
                {
                    "kind": bloom.type_name,
                    "bits": bloom.m_bits,
                    "hashes": bloom.k_hashes,
                    "fill": round(bloom.fill(), 6),
                    "estimated_items": None if estimate is None else round(estimate, 3),
                    "predicted_rate": round(bloom.predict_rate(), 8),
                    "saturated": bloom.is_saturated(),
                },
                sort_keys=True,
            )
        )
    else:
        for label, value in rows:
            print(f"{label:<18}{value}")
        if bloom.is_saturated():
            print("note                at this fill nearly every lookup answers yes")
    return EXIT_PRESENT if not bloom.is_saturated() else EXIT_ABSENT


def cmd_sized(args: argparse.Namespace) -> int:
    sizing = sized_for(args.expected, args.rate)
    if args.json:
        print(
            json.dumps(
                {
                    "expected": sizing.expected,
                    "fp_rate": sizing.fp_rate,
                    "m_bits": sizing.m_bits,
                    "k_hashes": sizing.k_hashes,
                    "predicted_rate": round(sizing.predicted_rate, 8),
                },
                sort_keys=True,
            )
        )
    else:
        for line in sizing.lines():
            print(line)
    return EXIT_PRESENT


def cmd_demo(args: argparse.Namespace) -> int:
    for line in render():
        print(line)
    return EXIT_PRESENT


def cmd_selftest(args: argparse.Namespace) -> int:
    from . import selftest

    return selftest.main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Probabilistic membership whose error rate you can measure.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="write a new, empty filter")
    create.add_argument("--filter", required=True, help="path of the filter file")
    create.add_argument("--expected", type=int, required=True, help="items it must hold")
    create.add_argument("--rate", type=float, default=0.01, help="target false-positive rate")
    create.add_argument("--kind", choices=("bloom", "counting"), default="bloom")
    create.add_argument("--force", action="store_true", help="replace an existing filter")
    create.set_defaults(func=cmd_create)

    add = sub.add_parser("add", help="add items to an existing filter")
    add.add_argument("--filter", required=True)
    add.add_argument("--item", action="append", required=True, help="repeatable")
    add.set_defaults(func=cmd_add)

    check = sub.add_parser("check", help="ask whether an item might be present")
    check.add_argument("--filter", required=True)
    check.add_argument("--item", required=True)
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=cmd_check)

    info = sub.add_parser("info", help="report fill, estimate and health")
    info.add_argument("--filter", required=True)
    info.add_argument("--json", action="store_true")
    info.set_defaults(func=cmd_info)

    sized = sub.add_parser("sized", help="print the bits and hashes a budget needs")
    sized.add_argument("--expected", type=int, required=True)
    sized.add_argument("--rate", type=float, default=0.01)
    sized.add_argument("--json", action="store_true")
    sized.set_defaults(func=cmd_sized)

    demo = sub.add_parser("demo", help="run the five measurements")
    demo.set_defaults(func=cmd_demo)

    selftest = sub.add_parser("selftest", help="check the filter against its own claims")
    selftest.set_defaults(func=cmd_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (BloomFilterError, UsageError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
