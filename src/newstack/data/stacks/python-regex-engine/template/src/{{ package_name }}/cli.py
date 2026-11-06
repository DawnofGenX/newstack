"""The command: one question per subcommand, and an exit code that answers it."""

from __future__ import annotations

import argparse
import json
import sys

from . import backtrack, demo, dfa, explain, nfa, syntax
from . import match as match_module

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NO_MATCH = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The question itself cannot be asked as given."""


def _pattern(text: str) -> syntax.Node:
    return syntax.parse(text)


def _match_payload(found: match_module.Match | None, text: str, pattern: str) -> dict:
    payload = {
        "pattern": pattern,
        "text": text,
        "matched": found is not None,
        "start": None,
        "end": None,
        "value": None,
    }
    if found is not None:
        payload["start"] = found.start
        payload["end"] = found.end
        payload["value"] = found.value
    return payload


def _command_match(args: argparse.Namespace) -> int:
    node = _pattern(args.pattern)
    machine = nfa.compile_node(node, args.pattern)
    held = machine.matches(args.text)
    if args.json:
        print(
            json.dumps(
                _match_payload(
                    match_module.Match(args.text, 0, len(args.text)) if held else None,
                    args.text,
                    node.render(),
                ),
                indent=2,
            )
        )
        return EXIT_OK if held else EXIT_NO_MATCH
    print(f"pattern    {node.render()}")
    print(f"text       {args.text!r}")
    print(f"verdict    {'the whole text matches' if held else 'no match for the whole text'}")
    print(f"machine    {machine.states} state(s), {machine.edge_count()} edge(s)")
    return EXIT_OK if held else EXIT_NO_MATCH


def _command_search(args: argparse.Namespace) -> int:
    node = _pattern(args.pattern)
    found = match_module.search(node, args.text)
    if args.json:
        print(json.dumps(_match_payload(found, args.text, node.render()), indent=2))
        return EXIT_OK if found is not None else EXIT_NO_MATCH
    for line in match_module.describe(node, args.text):
        print(line)
    if found is not None:
        print(f"prefix     the longest end at that start is column {found.end}")
    return EXIT_OK if found is not None else EXIT_NO_MATCH


def _command_explain(args: argparse.Namespace) -> int:
    node = _pattern(args.pattern)
    for line in explain.trace_lines(node, args.text):
        print(line)
    print()
    held = nfa.compile_node(node, args.pattern).matches(args.text)
    return EXIT_OK if held else EXIT_NO_MATCH


def _command_machine(args: argparse.Namespace) -> int:
    for line in explain.machine_lines(_pattern(args.pattern)):
        print(line)
    return EXIT_OK


def _command_dfa(args: argparse.Namespace) -> int:
    node = _pattern(args.pattern)
    automaton = dfa.determinize(node, args.pattern)
    if args.json:
        print(
            json.dumps(
                {
                    "pattern": node.render(),
                    "states": automaton.states,
                    "accepting": list(automaton.accepting),
                    "transitions": len(automaton.transitions),
                },
                indent=2,
            )
        )
        return EXIT_OK
    for line in automaton.lines():
        print(line)
    return EXIT_OK


def _command_agrees(args: argparse.Namespace) -> int:
    node = _pattern(args.pattern)
    verdict = dfa.agreement(node, alphabet=args.alphabet, longest=args.max_len)
    for line in verdict.lines():
        print(line)
    return EXIT_OK if verdict.held() else EXIT_NO_MATCH


def _command_why(args: argparse.Namespace) -> int:
    node = _pattern(args.pattern)
    for line in explain.verdict_lines(node, args.text):
        print(line)
    print()
    for line_of_trace in explain.trace_lines(node, args.text, limit=args.limit):
        print(line_of_trace)
    held = nfa.compile_node(node, args.pattern).matches(args.text)
    return EXIT_OK if held else EXIT_NO_MATCH


def _command_compare(args: argparse.Namespace) -> int:
    node = _pattern(args.pattern)
    machine = nfa.compile_node(node, args.pattern)
    steps = backtrack.count(node, args.text)
    print(f"pattern    {node.render()}")
    print(f"text       {args.text!r}")
    print(f"simulation {len(args.text) + 1} set(s) for {machine.states} state(s)")
    print(steps.line())
    if steps.capped:
        print("note       the backtracker was stopped by the step budget, not by the text")
    agrees = machine.matches(args.text) == steps.matched
    verdict = "both engines agree" if agrees else "THE ENGINES DISAGREE"
    print(f"verdict    {verdict}")
    return EXIT_OK if agrees else EXIT_NO_MATCH


def _command_demo(_args: argparse.Namespace) -> int:
    print(demo.render_stories())
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from . import selftest

    report = selftest.run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_NO_MATCH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A regular expression engine that never backtracks over its input.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    match_parser = subparsers.add_parser("match", help="does the pattern match the whole text")
    match_parser.add_argument("pattern")
    match_parser.add_argument("text")
    match_parser.add_argument("--json", action="store_true")
    match_parser.set_defaults(handler=_command_match)

    search_parser = subparsers.add_parser("search", help="the leftmost longest match in the text")
    search_parser.add_argument("pattern")
    search_parser.add_argument("text")
    search_parser.add_argument("--json", action="store_true")
    search_parser.set_defaults(handler=_command_search)

    explain_parser = subparsers.add_parser("explain", help="the state set after every character")
    explain_parser.add_argument("pattern")
    explain_parser.add_argument("text")
    explain_parser.set_defaults(handler=_command_explain)

    why_parser = subparsers.add_parser("why", help="the verdict first, then the trace")
    why_parser.add_argument("pattern")
    why_parser.add_argument("text")
    why_parser.add_argument("--limit", type=int, default=20)
    why_parser.set_defaults(handler=_command_why)

    machine_parser = subparsers.add_parser("machine", help="every state and its edges")
    machine_parser.add_argument("pattern")
    machine_parser.set_defaults(handler=_command_machine)

    dfa_parser = subparsers.add_parser("dfa", help="the determinised machine and its size")
    dfa_parser.add_argument("pattern")
    dfa_parser.add_argument("--json", action="store_true")
    dfa_parser.set_defaults(handler=_command_dfa)

    agrees_parser = subparsers.add_parser("agrees", help="compare both machines exhaustively")
    agrees_parser.add_argument("pattern")
    agrees_parser.add_argument("--alphabet", default=None)
    agrees_parser.add_argument("--max-len", type=int, default=5, dest="max_len")
    agrees_parser.set_defaults(handler=_command_agrees)

    compare_parser = subparsers.add_parser("compare", help="the simulation against a backtracker")
    compare_parser.add_argument("pattern")
    compare_parser.add_argument("text")
    compare_parser.set_defaults(handler=_command_compare)

    subparsers.add_parser("demo", help="six stories about the machines").set_defaults(
        handler=_command_demo
    )
    subparsers.add_parser("selftest", help="run the invariants").set_defaults(
        handler=_command_selftest
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "agrees" and args.max_len < 0:
        print(f"{PROGRAM}: --max-len must be zero or more", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        return args.handler(args)
    except syntax.PatternError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        if args.command in {"match", "search", "explain", "why", "compare"}:
            print(error.caret(getattr(args, "pattern", "")), file=sys.stderr)
        return EXIT_UNUSABLE
    except ValueError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
