"""The command line: check a history, shrink it, and prove the two checkers agree."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import history as history_module
from .check import brute_force, check, shrink
from .demo import render_stories
from .explain import verdict_lines
from .history import HistoryError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The command line asked for something it cannot answer."""


def _history(args: argparse.Namespace) -> history_module.History:
    history = history_module.load(Path(args.history))
    if args.initial is None:
        return history
    return history_module.History(
        operations=history.operations, initial=args.initial, source=history.source
    )


def _payload(history: history_module.History, verdict) -> dict[str, object]:
    return {
        "source": history.source,
        "initial": history.initial,
        "operations": [op.text() for op in history.operations],
        **verdict.as_dict(),
    }


def _command_check(args: argparse.Namespace) -> int:
    history = _history(args)
    verdict = check(history)
    if args.json:
        print(json.dumps(_payload(history, verdict), indent=2))
    else:
        print("\n".join(verdict_lines(history, verdict)))
    return EXIT_OK if verdict.linearizable else EXIT_REFUSED


def _command_shrink(args: argparse.Namespace) -> int:
    history = _history(args)
    core, verdict = shrink(history)
    if verdict.linearizable:
        print(f"{PROGRAM}: this history is linearizable, so there is nothing to shrink")
        return EXIT_OK
    print(f"core       {len(core)} of {len(history)} operation(s) from {history.source}")
    for op in core.operations:
        print(f"  {op.text()}")
    print(f"verdict    {verdict.verdict}")
    if args.json:
        print(json.dumps(_payload(core, verdict), indent=2))
    return EXIT_REFUSED


def _command_compare(args: argparse.Namespace) -> int:
    history = _history(args)
    if len(history) > 8:
        raise UsageError(
            f"compare runs every permutation, so it stops at 8 operations; "
            f"this history has {len(history)}"
        )
    fast = check(history)
    slow = brute_force(history)
    print(f"search     {fast.verdict:<16} {fast.nodes:>7} node(s)")
    print(f"yardstick  {slow.verdict:<16} {slow.nodes:>7} order(s) tried")
    agree = fast.verdict == slow.verdict
    print(f"verdict    {'the two checkers agree' if agree else 'THE TWO CHECKERS DISAGREE'}")
    return EXIT_OK if agree else EXIT_REFUSED


def _command_demo(args: argparse.Namespace) -> int:
    print("\n".join(render_stories()))
    return EXIT_OK


def _command_selftest(args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="Linearizability of a register history."
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("check", help="decide whether a history is linearizable")
    verify.add_argument("--history", required=True, help="a JSONL history")
    verify.add_argument(
        "--initial", type=int, default=None, help="the value before the first write"
    )
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(handler=_command_check)

    smaller = subparsers.add_parser("shrink", help="the smallest core that still fails")
    smaller.add_argument("--history", required=True)
    smaller.add_argument("--initial", type=int, default=None)
    smaller.add_argument("--json", action="store_true")
    smaller.set_defaults(handler=_command_shrink)

    compare = subparsers.add_parser("compare", help="the search against every permutation")
    compare.add_argument("--history", required=True)
    compare.add_argument("--initial", type=int, default=None)
    compare.set_defaults(handler=_command_compare)

    subparsers.add_parser("demo", help="six histories with their claims checked").set_defaults(
        handler=_command_demo
    )
    subparsers.add_parser("selftest", help="the same answers without pytest").set_defaults(
        handler=_command_selftest
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except UsageError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except HistoryError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except ValueError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
