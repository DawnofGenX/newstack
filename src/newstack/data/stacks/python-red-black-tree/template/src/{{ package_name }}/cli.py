"""The command line: keys in, sorted answers out, shape audited."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_keys, parse_key
from .demo import stories
from .keys import KeyError
from .tree import RBTree, TreeError
from .workload import WorkloadError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _tree(args: argparse.Namespace) -> RBTree:
    return RBTree(load_keys(args.keys))


def _keys_of(text: str) -> int:
    return parse_key(text)


def _payload(tree: RBTree, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "keys": tree.count(),
        "seated": tree.invariant(),
        "walk": tree.keys(),
    }
    payload.update(extra)
    return payload


def _command_add(args: argparse.Namespace) -> int:
    tree = _tree(args)
    asked = [_keys_of(text) for text in args.new_keys]
    added = sum(tree.insert(key) for key in asked)
    if args.json:
        print(json.dumps(_payload(tree, {"added": added}), indent=2))
    else:
        print(f"keys       {tree.count()} held, {added} added")
        for key in asked:
            stored = "stored" if tree.has(key) else "refused"
            print(f"  {key:<10} {stored}")
    return EXIT_OK


def _command_remove(args: argparse.Namespace) -> int:
    tree = _tree(args)
    asked = [_keys_of(text) for text in args.dropped]
    for key in asked:
        tree.remove(key)
    if args.json:
        print(json.dumps(_payload(tree, {"dropped": asked}), indent=2))
    else:
        print(f"keys       {tree.count()} held, {len(asked)} dropped")
        for key in asked:
            print(f"  {key:<10} removed")
    return EXIT_OK


def _command_has(args: argparse.Namespace) -> int:
    tree = _tree(args)
    asked = [_keys_of(text) for text in args.asked]
    found = all(tree.has(key) for key in asked)
    if args.json:
        held = {str(key): tree.has(key) for key in asked}
        print(json.dumps(_payload(tree, {"asked": held}), indent=2))
    else:
        for key in asked:
            mark = "key" if tree.has(key) else "not a key"
            print(f"{key:<12} {mark}")
    return EXIT_OK if found else EXIT_MISS


def _command_iter(args: argparse.Namespace) -> int:
    tree = _tree(args)
    walked = tree.keys()
    if args.json:
        print(json.dumps(_payload(tree, {"listed": len(walked)}), indent=2))
    else:
        print(f"keys       {len(walked)} listed, ascending")
        for line in walked:
            print(f"  {line}")
    return EXIT_OK if walked else EXIT_MISS


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


def _corpus_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--keys", required=True, help="one key per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A red-black tree over bounded integer keys: add, "
        "remove, has, iter, selftest, demo.",
    )
    parser.add_argument("--version", action="version",
                        version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="store keys in the tree")
    _corpus_args(add_parser)
    add_parser.add_argument("new_keys", nargs="+", metavar="KEY")
    add_parser.add_argument("--json", action="store_true")
    add_parser.set_defaults(handler=_command_add)

    remove_parser = subparsers.add_parser(
        "remove", help="drop keys the tree must hold"
    )
    _corpus_args(remove_parser)
    remove_parser.add_argument("dropped", nargs="+", metavar="KEY")
    remove_parser.add_argument("--json", action="store_true")
    remove_parser.set_defaults(handler=_command_remove)

    has_parser = subparsers.add_parser("has", help="membership, exactly")
    _corpus_args(has_parser)
    has_parser.add_argument("asked", nargs="+", metavar="KEY")
    has_parser.add_argument("--json", action="store_true")
    has_parser.set_defaults(handler=_command_has)

    iter_parser = subparsers.add_parser(
        "iter", help="the in-order walk, ascending"
    )
    _corpus_args(iter_parser)
    iter_parser.add_argument("--json", action="store_true")
    iter_parser.set_defaults(handler=_command_iter)

    selftest_parser = subparsers.add_parser("selftest", help="the invariants")
    selftest_parser.set_defaults(handler=_command_selftest)

    demo_parser = subparsers.add_parser("demo", help="six stories, live")
    demo_parser.set_defaults(handler=_command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (CorpusError, KeyError, TreeError, WorkloadError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
