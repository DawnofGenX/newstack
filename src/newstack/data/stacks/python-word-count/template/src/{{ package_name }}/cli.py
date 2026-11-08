"""The command line: one question per run, the oracle consulted first."""

from __future__ import annotations

import argparse
import json
import sys

from .solve import WordCountError, audit, count_words, longest_word, word_frequencies

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_count(args: argparse.Namespace) -> int:
    try:
        c = count_words(args.s)
    except WordCountError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(c))
        return EXIT_OK
    print(f"count_words   {c}")
    return EXIT_OK


def _command_freq(args: argparse.Namespace) -> int:
    try:
        f = word_frequencies(args.s)
    except WordCountError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(f))
        return EXIT_OK
    print(f"frequencies   {f}")
    return EXIT_OK


def _command_longest(args: argparse.Namespace) -> int:
    try:
        w = longest_word(args.s)
    except WordCountError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(w))
        return EXIT_OK
    print(f"longest       {w}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    breaks = audit(args.values)
    if breaks:
        for b in breaks:
            print(f"{PROGRAM}: {b}", file=sys.stderr)
        return EXIT_BROKE
    print(f"audit      {len(args.values)} values, 0 breaks")
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_BROKE


def _command_demo(_args: argparse.Namespace) -> int:
    told = demo_stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_BROKE


def demo_stories():
    from .demo import stories

    return stories()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="small strings, honestly counted.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    c = subparsers.add_parser("count", help="s, word count out")
    c.add_argument("s")
    c.add_argument("--json", action="store_true")
    c.set_defaults(handler=_command_count)

    f = subparsers.add_parser("freq", help="s, frequencies out")
    f.add_argument("s")
    f.add_argument("--json", action="store_true")
    f.set_defaults(handler=_command_freq)

    lw = subparsers.add_parser("longest", help="s, longest word out")
    lw.add_argument("s")
    lw.add_argument("--json", action="store_true")
    lw.set_defaults(handler=_command_longest)

    a = subparsers.add_parser("audit", help="strings, audited")
    a.add_argument("values", nargs="+")
    a.set_defaults(handler=_command_audit)

    st = subparsers.add_parser("selftest", help="the promises")
    st.set_defaults(handler=_command_selftest)

    d = subparsers.add_parser("demo", help="six stories, computed live")
    d.set_defaults(handler=_command_demo)
    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    try:
        return args.handler(args)
    except WordCountError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
