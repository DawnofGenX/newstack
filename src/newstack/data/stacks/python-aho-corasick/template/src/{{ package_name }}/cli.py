"""The command line: one question per run, and a ledger that names its order."""

from __future__ import annotations

import argparse
import json
import sys

from .automaton import AhoCorasick, AhoCorasickError
from .corpus import CorpusError, load_patterns, load_text, prose
from .naive import naive_sweep

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _machine(args: argparse.Namespace) -> AhoCorasick:
    return AhoCorasick(load_patterns(args.patterns))


def _payload(machine: AhoCorasick, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "patterns": list(machine.patterns),
        "states": machine.states,
        "depth": machine.depth,
    }
    payload.update(extra)
    return payload


def _command_build(args: argparse.Namespace) -> int:
    machine = _machine(args)
    if args.json:
        print(json.dumps(_payload(machine, {}), indent=2))
        return EXIT_OK
    print(f"patterns   {len(machine.patterns)} stated")
    print(f"states     {machine.states}, depth {machine.depth}")
    for pattern in machine.patterns:
        print(f"  {pattern}")
    return EXIT_OK


def _command_scan(args: argparse.Namespace) -> int:
    machine = _machine(args)
    text = load_text(args.text)
    sweep = machine.sweep(text)
    if args.json:
        print(
            json.dumps(
                _payload(
                    machine,
                    {
                        "text_length": sweep.text_length,
                        "states_crossed": sweep.states,
                        "hits": [
                            {"end": hit.end, "start": hit.start, "pattern": hit.pattern}
                            for hit in sweep.hits
                        ],
                    },
                ),
                indent=2,
            )
        )
    else:
        print(f"text       {sweep.text_length} characters")
        print(f"states     {sweep.states} crossed")
        print(f"hits       {len(sweep.hits)}")
        for hit in sweep.hits:
            print(f"  {hit.describe()}")
    return EXIT_OK if sweep.hits else EXIT_NONE


def _command_count(args: argparse.Namespace) -> int:
    machine = _machine(args)
    text = load_text(args.text)
    sweep = machine.sweep(text)
    naive = naive_sweep(text, machine.patterns)
    if args.json:
        print(
            json.dumps(
                _payload(
                    machine,
                    {
                        "text_length": sweep.text_length,
                        "hits": len(sweep.hits),
                        "states_crossed": sweep.states,
                        "naive_windows": naive.inspections,
                        "cheaper": sweep.states < naive.inspections,
                    },
                ),
                indent=2,
            )
        )
    else:
        print(f"text       {sweep.text_length} characters")
        print(f"hits       {len(sweep.hits)}")
        print(f"sweep      {sweep.states} state crossings")
        print(f"naive      {naive.inspections} windows inspected")
        print(f"cheaper    {sweep.states < naive.inspections}")
    return EXIT_OK if sweep.hits else EXIT_NONE


def _command_demo(_args: argparse.Namespace) -> int:
    machine = AhoCorasick(["the", "then", "hen", "there", "three", "here"])
    text = prose()
    sweep = machine.sweep(text)
    naive = naive_sweep(text, machine.patterns)
    if sweep.hits != naive.hits:
        print("the counter story lost its equal hits", file=sys.stderr)
        return EXIT_NONE
    print("corpus     the shipped prose, two halves of a seeded alphabet")
    print(f"patterns   {len(machine.patterns)}, states {machine.states}")
    print(f"hits       {len(sweep.hits)}, equal to the naive scan")
    print(f"sweep      {sweep.states} crossings vs naive {naive.inspections} windows")
    return EXIT_OK if sweep.hits and sweep.states < naive.inspections else EXIT_NONE


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_NONE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Multi-pattern matching: a trie, BFS failure links, one sweep.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser("build", help="build the automaton and state it")
    _corpus_args(build_parser_)
    build_parser_.add_argument("--json", action="store_true")
    build_parser_.set_defaults(handler=_command_build)

    scan_parser = subparsers.add_parser("scan", help="one sweep, every (pattern, end) hit")
    _corpus_args(scan_parser)
    scan_parser.add_argument("--text", required=True, help="the text to sweep")
    scan_parser.add_argument("--json", action="store_true")
    scan_parser.set_defaults(handler=_command_scan)

    count_parser = subparsers.add_parser("count", help="hits plus the ledger of the sweep")
    _corpus_args(count_parser)
    count_parser.add_argument("--text", required=True, help="the text to sweep")
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

    subparsers.add_parser("demo", help="the counter story on the shipped corpus").set_defaults(
        handler=_command_demo
    )
    subparsers.add_parser("selftest", help="run the invariants").set_defaults(
        handler=_command_selftest
    )
    return parser


def _corpus_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--patterns", required=True, help="one pattern per line")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (AhoCorasickError, CorpusError, UsageError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
