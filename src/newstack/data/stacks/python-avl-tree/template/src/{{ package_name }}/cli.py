"""The command line: one question per run, keys in walk order."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_keys
from .demo import stories
from .keys import KeysError
from .tree import AVLTree, TreeError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _tree(args: argparse.Namespace) -> AVLTree:  # type: ignore[no-untyped-def]
    return AVLTree(load_keys(args.keys))


def _payload(tree: AVLTree, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "keys": len(tree),
        "height": tree.height,
        "walk": tree.flatten(),
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
        print(f"keys       {len(tree)}")
        print(f"height     {tree.height}")
        print(f"walk       {_preview(tree.flatten())}")
    return EXIT_OK


def _command_remove(args: argparse.Namespace) -> int:
    tree = _tree(args)
    tree.remove(args.key)
    if args.json:
        print(json.dumps(_payload(tree, {"removed": args.key}), indent=2))
    else:
        print(f"removed    {args.key}")
        print(f"keys       {len(tree)}")
        print(f"height     {tree.height}")
        print(f"walk       {_preview(tree.flatten())}")
    return EXIT_OK


def _command_has(args: argparse.Namespace) -> int:
    tree = _tree(args)
    seated = args.key in tree
    if args.json:
        print(json.dumps(_payload(tree, {"key": args.key, "seated": seated}), indent=2))
    else:
        print(f"key        {args.key}")
        print(f"seated     {seated}")
    return EXIT_OK if seated else EXIT_MISS


def _command_iter(args: argparse.Namespace) -> int:
    tree = _tree(args)
    keys = tree.flatten()
    if args.json:
        print(json.dumps(_payload(tree, {}), indent=2))
    else:
        print(f"keys       {len(keys)}")
        print(f"height     {tree.height}")
        for key in keys:
            print(f"  {key}")
    return EXIT_OK


def _command_height(args: argparse.Namespace) -> int:
    tree = _tree(args)
    if args.json:
        print(json.dumps(_payload(tree, {}), indent=2))
    else:
        print(f"keys       {len(tree)}")
        print(f"height     {tree.height}")
    return EXIT_OK if len(tree) else EXIT_MISS


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
    parser.add_argument("--keys", required=True, help="one key per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Integer keys, height-balanced: add, remove, has, iter, height.",
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

    iter_parser = subparsers.add_parser("iter", help="the in-order walk")
    _key_args(iter_parser)
    iter_parser.add_argument("--json", action="store_true")
    iter_parser.set_defaults(handler=_command_iter)

    height_parser = subparsers.add_parser("height", help="the tree height")
    _key_args(height_parser)
    height_parser.add_argument("--json", action="store_true")
    height_parser.set_defaults(handler=_command_height)

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
