"""The command line: demo, merge, laws, selftest."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import __version__
from .clock import ClockError, Stamp
from .counter import CounterError, GCounter, PNCounter
from .demo import render
from .laws import check
from .orset import ORSet, ORSetError
from .register import LWWRegister, RegisterError

PROGRAM = "{{ npm_name }}"

EXIT_OK = 0
EXIT_BROKEN = 1
EXIT_UNUSABLE = 2


class UsageError(Exception):
    """An argument or a state file that cannot be used as given."""


def canon(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


PARSERS: dict[str, Callable[[object], Any]] = {
    "g-counter": GCounter.parse,
    "pn-counter": PNCounter.parse,
    "lww-register": LWWRegister.parse,
    "or-set": ORSet.parse,
}


def load_state(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise UsageError(f"cannot read {path}: {error.strerror or error}") from error
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise UsageError(f"{path} is not JSON: {error.msg} at line {error.lineno}") from error
    if not isinstance(payload, dict):
        raise UsageError(f"{path} holds a {type(payload).__name__}, not a state object")
    return payload


def merge_states(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    kind_left, kind_right = left.get("type"), right.get("type")
    if kind_left != kind_right:
        raise UsageError(
            f"cannot merge a {kind_left!r} state with a {kind_right!r} one: "
            "they are different lattices, and a merge between them has no answer"
        )
    parser = PARSERS.get(str(kind_left))
    if parser is None:
        known = ", ".join(sorted(PARSERS))
        raise UsageError(f"{kind_left!r} is not a state this tool merges ({known})")
    merged = parser(left).merge(parser(right))
    return merged.as_dict()


def law_suites() -> list[tuple[str, list[Any], Callable[[Any, Any], Any], Callable[[Any], str]]]:
    def serialise(state: Any) -> str:
        return canon(state.as_dict())

    return [
        (
            "g-counter",
            [GCounter(), GCounter({"a": 1}), GCounter({"b": 2}), GCounter({"a": 1, "b": 3})],
            GCounter.merge,
            serialise,
        ),
        (
            "pn-counter",
            [
                PNCounter(),
                PNCounter().increment("a", 3),
                PNCounter().decrement("b", 1),
                PNCounter().increment("a", 3).decrement("b", 1),
            ],
            PNCounter.merge,
            serialise,
        ),
        (
            "lww-register",
            [
                LWWRegister(),
                LWWRegister("red", Stamp(1_000, "a")),
                LWWRegister("blue", Stamp(1_000, "b")),
                LWWRegister("green", Stamp(2_000, "a")),
            ],
            LWWRegister.merge,
            serialise,
        ),
        (
            "or-set",
            [
                ORSet().add("x", "a"),
                ORSet().add("y", "b").add("x", "c"),
                ORSet().add("x", "a").remove("x"),
                ORSet().add("z", "d"),
            ],
            ORSet.merge,
            serialise,
        ),
    ]


def run_laws() -> int:
    failed = 0
    for kind, states, merge, serialise in law_suites():
        print(kind)
        for law in check(states, merge, serialise):
            print(law.line())
            failed += 0 if law.held else 1
        print("")
    if failed:
        print(f"laws: {failed} broken")
        return EXIT_BROKEN
    print("laws: all held")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Merge replicated state, and show what each merge guarantees.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("demo", help="six stories about what a merge can and cannot save")
    merge_parser = subparsers.add_parser("merge", help="merge two state files")
    merge_parser.add_argument("left", type=Path)
    merge_parser.add_argument("right", type=Path)
    subparsers.add_parser("laws", help="check the three laws on built-in states")
    subparsers.add_parser("selftest", help="run the built-in checks")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_usage(sys.stderr)
        print(f"{PROGRAM}: choose one of demo, merge, laws, selftest", file=sys.stderr)
        return EXIT_UNUSABLE

    try:
        if args.command == "demo":
            print("\n".join(render()))
            return EXIT_OK
        if args.command == "merge":
            merged = merge_states(load_state(args.left), load_state(args.right))
            print(json.dumps(merged, indent=2, sort_keys=True))
            return EXIT_OK
        if args.command == "laws":
            return run_laws()
        from .selftest import run

        return run()
    except (
        UsageError,
        ClockError,
        CounterError,
        ORSetError,
        RegisterError,
        OSError,
        ValueError,
    ) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
