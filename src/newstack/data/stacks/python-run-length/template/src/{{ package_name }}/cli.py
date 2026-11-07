"""The command line: one question per run, the loop checked before it answers."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_texts, report_lines
from .demo import stories
from .pairs import PairsError, pairs_from_json, pairs_to_json
from .rle import RunError, audit, decode, encode
from .text import TextError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _preview(pairs: list, limit: int = 12) -> str:
    rows = json.loads(pairs_to_json(pairs[:limit]))
    tail = "" if len(pairs) <= limit else f", ... ({len(pairs)} total)"
    return f"{rows}{tail}"


def _command_encode(args: argparse.Namespace) -> int:
    pairs = encode(args.text)
    breaks = audit(pairs)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(pairs_to_json(pairs))
    else:
        print(f"text       {len(args.text)} letters")
        print(f"pairs      {len(pairs)}")
        print(f"stream     {_preview(pairs)}")
    return EXIT_OK


def _command_decode(args: argparse.Namespace) -> int:
    pairs = pairs_from_json(args.stream)
    text = decode(pairs)
    if args.json:
        print(json.dumps({"pairs": len(pairs), "text": text}))
    else:
        print(f"pairs      {len(pairs)}")
        print(f"text       {text!r}")
    return EXIT_OK


def _command_roundtrip(args: argparse.Namespace) -> int:
    pairs = encode(args.text)
    back = decode(pairs)
    breaks = audit(pairs)
    closed = back == args.text and not breaks
    if args.json:
        payload = {
            "letters": len(args.text),
            "pairs": len(pairs),
            "closed": closed,
            "breaks": breaks,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"letters    {len(args.text)}")
        print(f"pairs      {len(pairs)}")
        print(f"closed     {closed}")
        for line in breaks[:5]:
            print(f"break      {line}")
    return EXIT_OK if closed else EXIT_BROKE


def _command_report(args: argparse.Namespace) -> int:
    texts = load_texts(args.corpus)
    for line in report_lines(texts):
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
        description="run-length over lowercase text: encode, decode, report.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_parser = subparsers.add_parser("encode", help="text in, pairs out")
    encode_parser.add_argument("text")
    encode_parser.add_argument("--json", action="store_true")
    encode_parser.set_defaults(handler=_command_encode)

    decode_parser = subparsers.add_parser("decode", help="pairs in, text out")
    decode_parser.add_argument("stream")
    decode_parser.add_argument("--json", action="store_true")
    decode_parser.set_defaults(handler=_command_decode)

    roundtrip_parser = subparsers.add_parser("roundtrip", help="the loop, checked live")
    roundtrip_parser.add_argument("text")
    roundtrip_parser.add_argument("--json", action="store_true")
    roundtrip_parser.set_defaults(handler=_command_roundtrip)

    report_parser = subparsers.add_parser("report", help="a corpus, counted")
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
    except (RunError, CorpusError, TextError, PairsError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
