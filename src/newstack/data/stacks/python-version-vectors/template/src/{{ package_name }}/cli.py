"""The command line: one comparison, one merge, one compaction, one matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import demo as demo_module
from . import selftest as selftest_module
from .prune import PruneError, compact, dominates_floor
from .vector import Relation, VectorError, VersionVector, explain

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_CONCURRENT = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """Something the command line could not make sense of."""


def _vector(text: str) -> VersionVector:
    try:
        return VersionVector.parse(text)
    except VectorError as error:
        raise UsageError(str(error)) from error


def _emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))


def _command_compare(arguments: argparse.Namespace) -> int:
    left = _vector(arguments.left)
    right = _vector(arguments.right)
    relation = left.compare(right)
    _emit(
        {
            "left": left.text(),
            "right": right.text(),
            "relation": relation.value,
            "explanation": explain(left, right),
        },
        arguments.json,
    )
    code = EXIT_CONCURRENT if relation is Relation.CONCURRENT else EXIT_OK
    if arguments.json:
        return code
    print(f"left         {left.text() or 'empty'}")
    print(f"right        {right.text() or 'empty'}")
    print(f"relation     {relation.value}")
    print(f"why          {explain(left, right)}")
    if relation is Relation.CONCURRENT:
        print("concurrent   neither write saw the other, so a rule has to pick one")
    return code


def _command_merge(arguments: argparse.Namespace) -> int:
    left = _vector(arguments.left)
    right = _vector(arguments.right)
    merged = left.merge(right)
    relation = left.compare(right)
    _emit(
        {
            "left": left.text(),
            "right": right.text(),
            "merged": merged.text(),
            "relation": relation.value,
        },
        arguments.json,
    )
    if arguments.json:
        return EXIT_OK
    print(f"left         {left.text() or 'empty'}")
    print(f"right        {right.text() or 'empty'}")
    print(f"relation     {relation.value}")
    print(f"merged       {merged.text() or 'empty'}")
    print(f"dominance    the merge is after both: {merged.compare(left) is Relation.AFTER}")
    return EXIT_OK


def _command_prune(arguments: argparse.Namespace) -> int:
    vector = _vector(arguments.vector)
    floor = _vector(arguments.floor)
    squeezed = compact(vector, floor)
    covered = dominates_floor(vector, floor)
    _emit(
        {
            "vector": vector.text(),
            "floor": floor.text(),
            "compacted": squeezed.text(),
            "dominates_floor": covered,
            "entries": len(vector),
            "kept": len(squeezed),
        },
        arguments.json,
    )
    code = EXIT_OK if covered else EXIT_CONCURRENT
    if arguments.json:
        return code
    print(f"vector       {vector.text() or 'empty'} ({len(vector)} entries)")
    print(f"floor        {floor.text() or 'empty'}")
    print(f"compacted    {squeezed.text() or 'empty'} ({len(squeezed)} entries)")
    print(f"dropped      {len(vector) - len(squeezed)}")
    if covered:
        print("sound        yes: this vector is above the floor, so the verdict survives")
    else:
        print("sound        NO: this vector is below the floor, so its verdict may change")
    return code


def load_vectors(path: str) -> list[tuple[str, VersionVector]]:
    """Read the ``{"name": ..., "vector": ...}`` JSONL form, in file order."""
    location = Path(path)
    if not location.exists():
        raise UsageError(f"no such file: {path}")
    rows: list[tuple[str, VersionVector]] = []
    for number, line in enumerate(location.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise UsageError(f"{path}: line {number} is not JSON: {error.msg}") from error
        if not isinstance(payload, dict) or "vector" not in payload:
            raise UsageError(f"{path}: line {number} needs a 'vector' field")
        name = str(payload.get("name") or f"row-{number}")
        rows.append((name, _vector(str(payload["vector"]))))
    if not rows:
        raise UsageError(f"{path} holds no vectors")
    return rows


def _command_pairs(arguments: argparse.Namespace) -> int:
    rows = load_vectors(arguments.vectors)
    width = max(len(name) for name, _ in rows)
    concurrent = 0
    table: list[dict[str, str]] = []
    lines: list[str] = [
        "vector        " + "  ".join(f"{name:<{max(width, 5)}}" for name, _ in rows)
    ]
    for left_name, left in rows:
        cells: list[str] = []
        for right_name, right in rows:
            if left_name == right_name:
                cells.append("-")
                continue
            relation = left.compare(right)
            if relation is Relation.CONCURRENT:
                concurrent += 1
            cells.append(
                {"equal": "=", "before": "<", "after": ">", "concurrent": "X"}[relation.value]
            )
        lines.append(
            f"{left_name:<{width}}  " + "  ".join(f"{cell:<{max(width, 5)}}" for cell in cells)
        )
    for position, (left_name, left) in enumerate(rows):
        for right_name, right in rows[position + 1 :]:
            table.append(
                {"left": left_name, "right": right_name, "relation": left.compare(right).value}
            )
    _emit(
        {"vectors": len(rows), "concurrent_pairs": concurrent // 2, "pairs": table}, arguments.json
    )
    code = EXIT_CONCURRENT if concurrent else EXIT_OK
    if arguments.json:
        return code
    for line in lines:
        print(line)
    print("legend        < before, > after, = equal, X concurrent")
    print(f"concurrent    {concurrent // 2} pair(s) out of {len(rows) * (len(rows) - 1) // 2}")
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Compare version vectors, merge them, and compact them against a floor.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    parser.set_defaults(handler=None)
    subparsers = parser.add_subparsers(dest="command")

    compare = subparsers.add_parser("compare", help="compare two vectors")
    compare.add_argument("--left", required=True, help="a vector, for example a:2,b:1")
    compare.add_argument("--right", required=True, help="the vector to compare against")
    compare.add_argument("--json", action="store_true", help="print the result as JSON")
    compare.set_defaults(handler=_command_compare)

    merge = subparsers.add_parser("merge", help="merge two vectors")
    merge.add_argument("--left", required=True)
    merge.add_argument("--right", required=True)
    merge.add_argument("--json", action="store_true")
    merge.set_defaults(handler=_command_merge)

    prune = subparsers.add_parser("prune", help="compact a vector against a floor")
    prune.add_argument("--vector", required=True)
    prune.add_argument("--floor", required=True)
    prune.add_argument("--json", action="store_true")
    prune.set_defaults(handler=_command_prune)

    pairs = subparsers.add_parser("pairs", help="print the relation matrix of a vector file")
    pairs.add_argument("--vectors", required=True, help="a JSONL file of {name, vector} rows")
    pairs.add_argument("--json", action="store_true")
    pairs.set_defaults(handler=_command_pairs)

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
    except (UsageError, VectorError, PruneError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
