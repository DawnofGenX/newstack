"""The command line: one question per run, the oracle checked before it answers."""

from __future__ import annotations

import argparse
import json
import sys

from .calc import value_of
from .corpus import CorpusError, load_records, report_lines
from .demo import stories
from .expr import ExprError
from .oracle import descent
from .yard import postfix_text, to_postfix

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_eval(args: argparse.Namespace) -> int:
    answer = value_of(args.expr)
    judged = descent(args.expr)
    if judged != answer:
        print(f"{PROGRAM}: the oracle answers {judged}, the yard {answer}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(json.dumps({"expr": args.expr, "value": answer, "oracle": judged}))
    else:
        print(f"expr       {args.expr}")
        print(f"value      {answer}")
        print(f"oracle     {judged}")
    return EXIT_OK


def _command_postfix(args: argparse.Namespace) -> int:
    queue = to_postfix(args.expr)
    if args.json:
        print(json.dumps({"expr": args.expr, "postfix": postfix_text(queue)}))
    else:
        print(f"expr       {args.expr}")
        print(f"postfix    {postfix_text(queue)}")
    return EXIT_OK


def _command_report(args: argparse.Namespace) -> int:
    records = load_records(args.corpus)
    for line in report_lines(records):
        print(line)
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_BROKE


def _command_demo(_args: argparse.Namespace) -> int:
    told = stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_BROKE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="infix to postfix and back: the yard, the oracle, the answer.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    eval_parser = subparsers.add_parser("eval", help="expression in, value out")
    eval_parser.add_argument("expr")
    eval_parser.add_argument("--json", action="store_true")
    eval_parser.set_defaults(handler=_command_eval)

    postfix_parser = subparsers.add_parser("postfix", help="expression in, queue out")
    postfix_parser.add_argument("expr")
    postfix_parser.add_argument("--json", action="store_true")
    postfix_parser.set_defaults(handler=_command_postfix)

    report_parser = subparsers.add_parser("report", help="a ledger, audited")
    report_parser.add_argument("--corpus", required=True)
    report_parser.set_defaults(handler=_command_report)

    selftest_parser = subparsers.add_parser("selftest", help="the invariants")
    selftest_parser.set_defaults(handler=_command_selftest)

    demo_parser = subparsers.add_parser("demo", help="six stories, computed live")
    demo_parser.set_defaults(handler=_command_demo)
    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (ExprError, CorpusError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
