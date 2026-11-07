"""The command line: one question per run, the loop checked before it answers."""

from __future__ import annotations

import argparse
import json
import sys

from .coder import CoderError, audit, compress, decompress
from .corpus import CorpusError, load_texts, report_lines
from .demo import stories
from .text import TextError
from .tokens import (
    TokenError,
    tokens_from_json,
    tokens_to_json,
)

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _preview(tokens: list, limit: int = 12) -> str:
    rows = json.loads(tokens_to_json(tokens[:limit]))
    tail = "" if len(tokens) <= limit else f", ... ({len(tokens)} total)"
    return f"{rows}{tail}"


def _command_compress(args: argparse.Namespace) -> int:
    tokens = compress(args.text)
    breaks = audit(tokens)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(tokens_to_json(tokens))
    else:
        print(f"text       {len(args.text)} letters")
        print(f"tokens     {len(tokens)}")
        print(f"stream     {_preview(tokens)}")
    return EXIT_OK


def _command_decompress(args: argparse.Namespace) -> int:
    tokens = tokens_from_json(args.stream)
    text = decompress(tokens)
    if args.json:
        print(json.dumps({"tokens": len(tokens), "text": text}))
    else:
        print(f"tokens     {len(tokens)}")
        print(f"text       {text!r}")
    return EXIT_OK


def _command_roundtrip(args: argparse.Namespace) -> int:
    tokens = compress(args.text)
    back = decompress(tokens)
    breaks = audit(tokens)
    closed = back == args.text and not breaks
    if args.json:
        payload = {
            "letters": len(args.text),
            "tokens": len(tokens),
            "closed": closed,
            "breaks": breaks,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"letters    {len(args.text)}")
        print(f"tokens     {len(tokens)}")
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
        description="LZ77 over lowercase text: compress, decompress, report.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compress_parser = subparsers.add_parser("compress", help="text in, tokens out")
    compress_parser.add_argument("text")
    compress_parser.add_argument("--json", action="store_true")
    compress_parser.set_defaults(handler=_command_compress)

    decompress_parser = subparsers.add_parser("decompress", help="tokens in, text out")
    decompress_parser.add_argument("stream")
    decompress_parser.add_argument("--json", action="store_true")
    decompress_parser.set_defaults(handler=_command_decompress)

    roundtrip_parser = subparsers.add_parser("roundtrip", help="the loop, checked live")
    roundtrip_parser.add_argument("text")
    roundtrip_parser.add_argument("--json", action="store_true")
    roundtrip_parser.set_defaults(handler=_command_roundtrip)

    report_parser = subparsers.add_parser("report", help="a corpus, priced")
    report_parser.add_argument("--corpus", required=True)
    report_parser.set_defaults(handler=_command_report)

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
    except (CoderError, CorpusError, TextError, TokenError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
