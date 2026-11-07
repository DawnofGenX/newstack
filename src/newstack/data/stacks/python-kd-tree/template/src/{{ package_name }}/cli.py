"""The command line: one question per run, and answers equal to the scan's."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_points, parse_point
from .demo import stories
from .points import PointError, describe
from .tree import KDTree, TreeError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _tree(args: argparse.Namespace) -> KDTree:
    return KDTree(load_points(args.points))


def _rect(text: str) -> tuple[int, int, int, int]:
    parts = text.split(",")
    if len(parts) != 4:
        raise CorpusError(f"not a rectangle: {text!r} is not x1,y1,x2,y2")
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
    except ValueError as error:
        raise CorpusError(f"not a rectangle: {text!r} holds {error}") from error


def _payload(tree: KDTree, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "points": len(tree),
        "corpus": [list(point) for point in sorted(tree.walk())],
    }
    payload.update(extra)
    return payload


def _render(points: list[tuple[int, int]]) -> list[str]:
    return [f"  {describe(point)}" for point in points]


def _command_add(args: argparse.Namespace) -> int:
    tree = _tree(args)
    asked = [parse_point(text) for text in args.new_points]
    added = sum(tree.insert(point) for point in asked)
    if args.json:
        print(json.dumps(_payload(tree, {"added": added}), indent=2))
    else:
        print(f"points     {len(tree)} held, {added} added")
        for point in asked:
            stored = "stored" if tree.has(point) else "refused"
            print(f"  {describe(point)}  {stored}")
    return EXIT_OK


def _command_has(args: argparse.Namespace) -> int:
    tree = _tree(args)
    asked = [parse_point(text) for text in args.asked]
    found = all(tree.has(point) for point in asked)
    if args.json:
        held = {
            describe(point): tree.has(point) for point in asked
        }
        print(json.dumps(_payload(tree, {"asked": held}), indent=2))
    else:
        for point in asked:
            mark = "point" if tree.has(point) else "not a point"
            print(f"{describe(point):<12} {mark}")
    return EXIT_OK if found else EXIT_MISS


def _command_range(args: argparse.Namespace) -> int:
    tree = _tree(args)
    box = _rect(args.rect)
    found = tree.range(box)
    if args.json:
        payload = _payload(tree, {
            "rect": list(box),
            "count": len(found),
            "listing": [list(point) for point in found],
        })
        print(json.dumps(payload, indent=2))
    else:
        print(f"rect       {describe((box[0], box[1]))} to "
              f"{describe((box[2], box[3]))}")
        print(f"inside     {len(found)} point(s)")
        for line in _render(found):
            print(line)
    return EXIT_OK if found else EXIT_MISS


def _command_nearest(args: argparse.Namespace) -> int:
    tree = _tree(args)
    query = parse_point(args.query)
    answer = tree.nearest(query)
    if args.json:
        payload = _payload(tree, {
            "query": list(query),
            "nearest": None if answer is None else list(answer),
        })
        print(json.dumps(payload, indent=2))
    else:
        print(f"query      {describe(query)}")
        if answer is None:
            print("nearest    nothing, the tree is empty")
        else:
            from .tree import distance
            print(f"nearest    {describe(answer)} at "
                  f"{distance(answer, query)} squared")
    return EXIT_OK if answer is not None else EXIT_MISS


def _command_count(args: argparse.Namespace) -> int:
    tree = _tree(args)
    if args.json:
        print(json.dumps(_payload(tree, {"seated": tree.invariant()}), indent=2))
    else:
        print(f"points     {len(tree)} held")
        print(f"seated     {tree.invariant()}, splits divide")
    return EXIT_OK


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
    parser.add_argument("--points", required=True, help="one x,y per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A 2-d kd-tree over integer point pairs: add, has, "
        "range, nearest, count.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="store points in the tree")
    _corpus_args(add_parser)
    add_parser.add_argument("new_points", nargs="+", metavar="X,Y")
    add_parser.add_argument("--json", action="store_true")
    add_parser.set_defaults(handler=_command_add)

    has_parser = subparsers.add_parser("has", help="membership, exactly")
    _corpus_args(has_parser)
    has_parser.add_argument("asked", nargs="+", metavar="X,Y")
    has_parser.add_argument("--json", action="store_true")
    has_parser.set_defaults(handler=_command_has)

    range_parser = subparsers.add_parser(
        "range", help="every point inside a rectangle, in order"
    )
    _corpus_args(range_parser)
    range_parser.add_argument("rect", metavar="X1,Y1,X2,Y2")
    range_parser.add_argument("--json", action="store_true")
    range_parser.set_defaults(handler=_command_range)

    nearest_parser = subparsers.add_parser(
        "nearest", help="the closest point, ties to the smallest"
    )
    _corpus_args(nearest_parser)
    nearest_parser.add_argument("query", metavar="X,Y")
    nearest_parser.add_argument("--json", action="store_true")
    nearest_parser.set_defaults(handler=_command_nearest)

    count_parser = subparsers.add_parser("count", help="size and seating")
    _corpus_args(count_parser)
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

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
    except (CorpusError, PointError, TreeError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
