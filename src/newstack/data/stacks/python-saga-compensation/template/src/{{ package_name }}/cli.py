"""Command line entry point: run the demo saga and report what actually happened.

Exit codes are the contract. ``0`` completed, ``1`` rolled back cleanly, ``2``
a rollback that left something standing, ``3`` the tool could not read its own
journal or arguments. A run that ends ``2`` is not "mostly fine": something the
saga did is still true, and whoever reads the exit code has to know that.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import demo, journal
from .runner import COMPLETED, INCOMPLETE, ROLLED_BACK, SagaError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_COMPLETED = 0
EXIT_ROLLED_BACK = 1
EXIT_INCOMPLETE = 2
EXIT_UNUSABLE = 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="Run a saga forward and unwind it on failure."
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="run the demo booking saga")
    run.add_argument("--journal", default="saga.jsonl", help="journal file to append to")
    run.add_argument("--saga", default="book-trip", help="saga id, and the journal's key")
    run.add_argument("--decline", default="book-flight", help="step that fails ('' for none)")
    run.add_argument("--break-compensation", default="", help="compensation that always fails")
    run.add_argument("--flaky-compensation", default="", help="compensation that fails once")
    run.add_argument("--json", action="store_true", help="print the outcome as JSON")

    state = sub.add_parser("journal", help="print what a journal says about a saga")
    state.add_argument("--journal", default="saga.jsonl")
    state.add_argument("--saga", default="book-trip")
    state.add_argument("--json", action="store_true")

    show = sub.add_parser("demo", help="run all four scenarios in a temporary directory")
    show.add_argument("--json", action="store_true")

    sub.add_parser("selftest", help="exercise the runner against a temporary journal")
    return parser


def _run(args: argparse.Namespace) -> int:
    decline = args.decline or None
    saga = demo.build(
        args.journal,
        decline_at=decline,
        break_compensation=args.break_compensation or None,
        flaky_compensation=args.flaky_compensation or None,
        saga_id=args.saga,
    )
    outcome = saga.run()
    if args.json:
        print(json.dumps(outcome.as_dict(), indent=2, sort_keys=True))
    else:
        for line in outcome.lines():
            print(line)
        calls = saga.state["calls"].names
        print(f"calls      {' -> '.join(calls)}")
    return {
        COMPLETED: EXIT_COMPLETED,
        ROLLED_BACK: EXIT_ROLLED_BACK,
        INCOMPLETE: EXIT_INCOMPLETE,
    }[outcome.status]


def _code_for(outcome: str | None) -> int:
    """The exit code for a journaled outcome: the same contract as a live run."""
    return {
        COMPLETED: EXIT_COMPLETED,
        ROLLED_BACK: EXIT_ROLLED_BACK,
        INCOMPLETE: EXIT_INCOMPLETE,
    }.get(outcome or "", EXIT_UNUSABLE)


def _journal(args: argparse.Namespace) -> int:
    records = journal.read(args.journal)
    saga = journal.Journal(args.journal)
    statuses = saga.statuses(args.saga)
    outcome = saga.outcome(args.saga)
    if args.json:
        payload = {
            "journal": str(Path(args.journal)),
            "saga": args.saga,
            "outcome": outcome,
            "steps": statuses,
            "records": len(records),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return _code_for(outcome)
    if not records:
        print(f"{args.journal}: empty or missing")
        return EXIT_UNUSABLE
    print(f"journal    {args.journal} ({len(records)} record(s))")
    print(f"saga       {args.saga}")
    print(f"outcome    {outcome or 'in progress or abandoned'}")
    for name, status in statuses.items():
        print(f"step       {name:<20} {status}")
    return _code_for(outcome)


def _demo(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="saga-demo-") as directory:
        worst = EXIT_COMPLETED
        for title, factory in demo.scenarios(directory):
            saga = factory()
            outcome = saga.run()
            print(f"-- {title}")
            for line in outcome.lines():
                print(f"   {line}")
            print(f"   calls      {' -> '.join(saga.state['calls'].names)}")
            code = {
                COMPLETED: EXIT_COMPLETED,
                ROLLED_BACK: EXIT_ROLLED_BACK,
                INCOMPLETE: EXIT_INCOMPLETE,
            }[outcome.status]
            worst = max(worst, code)
            print()
    return worst


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_UNUSABLE
    try:
        if args.command == "run":
            return _run(args)
        if args.command == "journal":
            return _journal(args)
        if args.command == "demo":
            return _demo(args)
        from . import selftest

        return selftest.main()
    except (SagaError, journal.JournalError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
