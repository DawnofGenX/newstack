"""A small terminal front end: parse, allocate, split, selftest.

The library is the product; the CLI exists so the arithmetic can be checked by eye in a code
review, with the minor units printed next to the formatted amount.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import allocation, parse
from . import selftest as selftest_mod
from .errors import MoneyError
from .model import Money, currency_of

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_UNUSABLE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Money in minor units: parse it, allocate it, prove it balances.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser("parse", help="parse '12.34 USD' into minor units")
    parse_parser.add_argument("text", help="amount and currency code, e.g. '12.34 USD'")
    parse_parser.add_argument("--round", dest="rounding", default=None, help="rounding mode")
    parse_parser.add_argument("--json", action="store_true", help="print JSON")

    alloc_parser = subparsers.add_parser("alloc", help="split an amount by ratios")
    alloc_parser.add_argument("text", help="amount and currency code, e.g. '100.00 USD'")
    alloc_parser.add_argument("ratios", nargs="+", type=int, help="integer weights")
    alloc_parser.add_argument("--round", dest="rounding", default=None, help="rounding mode")

    split_parser = subparsers.add_parser("split", help="split an amount into equal parts")
    split_parser.add_argument("text", help="amount and currency code")
    split_parser.add_argument("parts", type=int, help="number of shares")

    subparsers.add_parser("selftest", help="run the built-in checks")
    return parser


def describe(money: Money) -> str:
    currency = currency_of(money.currency)
    return f"minor {money.amount:>8}  exponent {currency.exponent}  {money.format()}"


def command_parse(args: argparse.Namespace) -> int:
    money = parse.parse(args.text, args.rounding)
    if args.json:
        currency = currency_of(money.currency)
        payload = {
            "amount": money.amount,
            "currency": money.currency,
            "exponent": currency.exponent,
            "formatted": money.format(),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(describe(money))
    return EXIT_OK


def command_alloc(args: argparse.Namespace) -> int:
    money = parse.parse(args.text, args.rounding)
    parts = allocation.allocate(money, args.ratios)
    for index, part in enumerate(parts):
        print(f"share {index}  ratio {args.ratios[index]:>4}  {part.format()}")
    total = Money(sum(part.amount for part in parts), money.currency)
    print(f"total       {total.format()}  (wanted {money.format()})")
    print(f"balances    {'yes' if total.amount == money.amount else 'no'}")
    return EXIT_OK if total.amount == money.amount else EXIT_UNUSABLE


def command_split(args: argparse.Namespace) -> int:
    money = parse.parse(args.text)
    for index, part in enumerate(allocation.split(money, args.parts)):
        print(f"share {index}  {part.format()}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "parse":
            return command_parse(args)
        if args.command == "alloc":
            return command_alloc(args)
        if args.command == "split":
            return command_split(args)
        if args.command == "selftest":
            return selftest_mod.run()
    except (MoneyError, TypeError, ValueError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    return EXIT_UNUSABLE
