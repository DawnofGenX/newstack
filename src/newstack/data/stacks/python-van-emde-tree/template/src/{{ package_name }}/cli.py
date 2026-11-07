"""The command line: one question per run, answers the scan owes."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_keys
from .demo import stories
from .keys import KeysError
from .tree import TreeError, VanEmdeTree

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _tree(args: argparse.Namespace) -> VanEmdeTree:  # type: ignore[no-untyped-def]
    return VanEmdeTree(load_keys(args.keys))


def _payload(tree: VanEmdeTree, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "seats": len(tree),
        "min": tree.minimum(),
        "max": tree.maximum(),
        "live": tree.live(),
    }
    payload.update(extra)
    return payload


def _preview(keys: list[int], limit: int = 20) -> str:
    shown = keys[:limit]
    tail = "" if len(keys) <= limit else f", ... ({len(keys)} total)"
    return f"{shown}{tail}"


def _command_add(args: argparse.Namespace) -> int:
    tree = _tree(args)
    tree.insert(args.key)
    if args.json:
        print(json.dumps(_payload(tree, {"seated": args.key}), indent=2))
    else:
        print(f"key        {args.key}")
        print(f"seats      {len(tree)}")
        print(f"live       {_preview(tree.live())}")
    return EXIT_OK


def _command_remove(args: argparse.Namespace) -> int:
    tree = _tree(args)
    tree.remove(args.key)
    if args.json:
        print(json.dumps(_payload(tree, {"removed": args.key}), indent=2))
    else:
        print(f"removed    {args.key}")
        print(f"seats      {len(tree)}")
        print(f"live       {_preview(tree.live())}")
    return EXIT_OK


def _command_has(args: argparse.Namespace) -> int:
    tree = _tree(args)
    seated = tree.member(args.key)
    if args.json:
        print(json.dumps(_payload(tree, {"key": args.key, "seated": seated}), indent=2))
    else:
        print(f"key        {args.key}")
        print(f"seated     {seated}")
    return EXIT_OK if seated else EXIT_MISS


def _command_succ(args: argparse.Namespace) -> int:
    tree = _tree(args)
    found = tree.successor(args.key)
    if args.json:
        print(json.dumps(_payload(tree, {"query": args.key, "successor": found}), indent=2))
    else:
        print(f"query      {args.key}")
        print(f"successor  {found}")
    return EXIT_OK if found is not None else EXIT_MISS


def _command_pred(args: argparse.Namespace) -> int:
    tree = _tree(args)
    found = tree.predecessor(args.key)
    if args.json:
        print(
            json.dumps(_payload(tree, {"query": args.key, "predecessor": found}), indent=2)
        )
    else:
        print(f"query       {args.key}")
        print(f"predecessor {found}")
    return EXIT_OK if found is not None else EXIT_MISS


def _command_min(args: argparse.Namespace) -> int:
    tree = _tree(args)
    found = tree.minimum()
    if args.json:
        print(json.dumps(_payload(tree, {}), indent=2))
    else:
        print(f"min        {found}")
    return EXIT_OK if found is not None else EXIT_MISS


def _command_max(args: argparse.Namespace) -> int:
    tree = _tree(args)
    found = tree.maximum()
    if args.json:
        print(json.dumps(_payload(tree, {}), indent=2))
    else:
        print(f"max        {found}")
    return EXIT_OK if found is not None else EXIT_MISS


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_MISS


def _command_demo(_args: argparse.Namespace) -> int:
    told = stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_MISS


def _key_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--keys", required=True, help="one seat per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Seats in [0, 256): add, remove, has, succ, pred, min, max.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="seat a key")
    _key_args(add_parser)
    add_parser.add_argument("key", type=int)
    add_parser.add_argument("--json", action="store_true")
    add_parser.set_defaults(handler=_command_add)

    remove_parser = subparsers.add_parser("remove", help="unseat a key")
    _key_args(remove_parser)
    remove_parser.add_argument("key", type=int)
    remove_parser.add_argument("--json", action="store_true")
    remove_parser.set_defaults(handler=_command_remove)

    has_parser = subparsers.add_parser("has", help="is a key seated")
    _key_args(has_parser)
    has_parser.add_argument("key", type=int)
    has_parser.add_argument("--json", action="store_true")
    has_parser.set_defaults(handler=_command_has)

    succ_parser = subparsers.add_parser("succ", help="smallest seat >= key")
    _key_args(succ_parser)
    succ_parser.add_argument("key", type=int)
    succ_parser.add_argument("--json", action="store_true")
    succ_parser.set_defaults(handler=_command_succ)

    pred_parser = subparsers.add_parser("pred", help="largest seat <= key")
    _key_args(pred_parser)
    pred_parser.add_argument("key", type=int)
    pred_parser.add_argument("--json", action="store_true")
    pred_parser.set_defaults(handler=_command_pred)

    min_parser = subparsers.add_parser("min", help="the smallest seat")
    _key_args(min_parser)
    min_parser.add_argument("--json", action="store_true")
    min_parser.set_defaults(handler=_command_min)

    max_parser = subparsers.add_parser("max", help="the largest seat")
    _key_args(max_parser)
    max_parser.add_argument("--json", action="store_true")
    max_parser.set_defaults(handler=_command_max)

    selftest_parser = subparsers.add_parser("selftest", help="the invariants")
    selftest_parser.set_defaults(handler=_command_selftest)

    demo_parser = subparsers.add_parser("demo", help="six stories, computed live")
    demo_parser.set_defaults(handler=_command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (CorpusError, KeysError, TreeError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
