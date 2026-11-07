"""The command line: one question per run, the loop checked before it answers."""

from __future__ import annotations

import argparse
import json
import sys

from .coder import CoderError, decode, encode, size_report
from .corpus import CorpusError, load_texts, report_lines
from .demo import stories
from .freq import FrequencyError, tally
from .table import TableError, audit, code_table
from .text import TextError
from .tree import TreeError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_encode(args: argparse.Namespace) -> int:
    bits = encode(args.text)
    if args.json:
        print(json.dumps({"letters": len(args.text), "bits": bits}))
    else:
        print(f"letters    {len(args.text)}")
        print(f"bits       {bits or '(none)'}")
    return EXIT_OK


def _command_decode(args: argparse.Namespace) -> int:
    table = code_table(tally(args.text))
    text = decode(args.bits, table)
    if args.json:
        print(json.dumps({"bits": len(args.bits), "text": text}))
    else:
        print(f"bits       {len(args.bits)}")
        print(f"text       {text!r}")
    return EXIT_OK


def _command_frequencies(args: argparse.Namespace) -> int:
    counts = tally(args.text)
    if args.json:
        print(json.dumps(counts))
    else:
        for letter, weight in counts.items():
            print(f"{letter}        {weight}")
    return EXIT_OK


def _command_report(args: argparse.Namespace) -> int:
    for line in report_lines(load_texts(args.corpus)):
        print(line)
    return EXIT_OK


def _command_roundtrip(args: argparse.Namespace) -> int:
    letters, bits, book = size_report(args.text)
    back = decode(encode(args.text, book), book) if args.text else ""
    clean = audit(book)
    closed = back == args.text and not clean
    if args.json:
        payload = {
            "letters": letters,
            "bits": bits,
            "words": len(book.codes),
            "closed": closed,
            "breaks": clean,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"letters    {letters}")
        print(f"bits       {bits}")
        print(f"words      {len(book.codes)}")
        print(f"closed     {closed}")
        for line in clean[:5]:
            print(f"break      {line}")
    return EXIT_OK if closed else EXIT_BROKE


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
        description="Canonical Huffman over lowercase text: encode, decode, report.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_parser = subparsers.add_parser("encode", help="text in, bits out")
    encode_parser.add_argument("text")
    encode_parser.add_argument("--json", action="store_true")
    encode_parser.set_defaults(handler=_command_encode)

    decode_parser = subparsers.add_parser("decode", help="bits and text in, letters out")
    decode_parser.add_argument("bits")
    decode_parser.add_argument("text", help="the text whose weights built the table")
    decode_parser.add_argument("--json", action="store_true")
    decode_parser.set_defaults(handler=_command_decode)

    frequencies_parser = subparsers.add_parser("frequencies", help="text in, weights out")
    frequencies_parser.add_argument("text")
    frequencies_parser.add_argument("--json", action="store_true")
    frequencies_parser.set_defaults(handler=_command_frequencies)

    report_parser = subparsers.add_parser("report", help="a corpus, priced")
    report_parser.add_argument("--corpus", required=True)
    report_parser.set_defaults(handler=_command_report)

    roundtrip_parser = subparsers.add_parser("roundtrip", help="the loop, checked live")
    roundtrip_parser.add_argument("text")
    roundtrip_parser.add_argument("--json", action="store_true")
    roundtrip_parser.set_defaults(handler=_command_roundtrip)

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
    except (
        CoderError,
        CorpusError,
        FrequencyError,
        TableError,
        TextError,
        TreeError,
    ) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
