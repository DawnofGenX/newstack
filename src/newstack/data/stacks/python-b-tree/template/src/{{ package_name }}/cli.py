"""The command line: one question per run, and a report that names the band."""

from __future__ import annotations

import argparse
import json
import sys

from .btree import BTree, BTreeError
from .corpus import CorpusError, load_keys
from .page import PageError, page_pair

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _tree(args: argparse.Namespace) -> BTree:
    return BTree(args.order, load_keys(args.keys))


def _payload(tree: BTree, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "order": tree.order,
        "band": [tree.min_keys, tree.max_keys],
        "corpus": len(tree),
        "height": tree.height,
        "leaf_levels": tree.leaf_levels,
        "keys": tree.keys,
    }
    payload.update(extra)
    return payload


def _command_load(args: argparse.Namespace) -> int:
    tree = _tree(args)
    if args.json:
        print(json.dumps(_payload(tree, {}), indent=2))
        return EXIT_OK
    print(f"order      {tree.order}, band [{tree.min_keys}..{tree.max_keys}]")
    print(f"corpus     {len(tree)} key(s)")
    print(f"height     {tree.height}, leaf levels {tree.leaf_levels}")
    for key in tree.keys:
        print(f"  {key}")
    return EXIT_OK


def _command_lookup(args: argparse.Namespace) -> int:
    tree = _tree(args)
    held = tree.lookup(args.key)
    if args.json:
        print(json.dumps(_payload(tree, {"key": args.key, "held": held}), indent=2))
    else:
        print(f"key        {args.key}")
        print(f"held       {held}")
    return EXIT_OK if held else EXIT_NONE


def _command_scan(args: argparse.Namespace) -> int:
    tree = _tree(args)
    found = tree.range_scan(args.low, args.high)
    if args.json:
        print(
            json.dumps(
                _payload(tree, {"window": [args.low, args.high], "found": found}),
                indent=2,
            )
        )
    else:
        print(f"window     [{args.low}..{args.high}]")
        print(f"found      {len(found)} key(s)")
        for key in found:
            print(f"  {key}")
    return EXIT_OK if found else EXIT_NONE


def _command_page(args: argparse.Namespace) -> int:
    tree = _tree(args)
    report = page_pair(tree, args.out)
    if args.json:
        print(
            json.dumps(
                {
                    "nodes": report.nodes,
                    "record": report.record,
                    "width": report.width,
                    "identical": report.identical,
                },
                indent=2,
            )
        )
    else:
        for line in report.lines():
            print(line)
    return EXIT_OK if report.identical else EXIT_NONE


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_NONE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A keyed B-tree of configurable order: insert, delete, look up, scan.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser("load", help="build a tree and walk it in order")
    _corpus_args(load_parser)
    load_parser.add_argument("--json", action="store_true")
    load_parser.set_defaults(handler=_command_load)

    lookup_parser = subparsers.add_parser("lookup", help="exact lookup of one key")
    _corpus_args(lookup_parser)
    lookup_parser.add_argument("--key", type=int, required=True)
    lookup_parser.add_argument("--json", action="store_true")
    lookup_parser.set_defaults(handler=_command_lookup)

    scan_parser = subparsers.add_parser("scan", help="every key in a window, ascending")
    _corpus_args(scan_parser)
    scan_parser.add_argument("--low", type=int, required=True)
    scan_parser.add_argument("--high", type=int, required=True)
    scan_parser.add_argument("--json", action="store_true")
    scan_parser.set_defaults(handler=_command_scan)

    page_parser = subparsers.add_parser(
        "page", help="freeze the tree into a page file and read it back"
    )
    _corpus_args(page_parser)
    page_parser.add_argument("--out", required=True)
    page_parser.add_argument("--json", action="store_true")
    page_parser.set_defaults(handler=_command_page)

    subparsers.add_parser("selftest", help="run the invariants").set_defaults(
        handler=_command_selftest
    )
    return parser


def _corpus_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--keys", required=True, help="one integer per line")
    parser.add_argument("--order", type=int, default=3, help="minimum degree, 2 or more")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (BTreeError, CorpusError, PageError, UsageError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
