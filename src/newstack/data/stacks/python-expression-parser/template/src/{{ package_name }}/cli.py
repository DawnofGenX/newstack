"""The command line: parse, evaluate, explain, and say which column went wrong."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation

from . import nodes
from .demo import render_stories
from .evaluator import PRECISION, EvalError, as_text, evaluate
from .lexer import LexError
from .nodes import Binary, Call, Name, Number, Unary, depth, tree_lines, walk
from .parser import ParseError, parse, precedence_table

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_UNUSABLE = 2


class UsageError(Exception):
    """The command was asked for something it does not do."""


def _definition(text: str) -> tuple[str, Decimal]:
    name, separator, raw = text.partition("=")
    if not separator or not name.strip():
        raise UsageError(f"--var wants name=value, not {text!r}")
    name = name.strip()
    if not (name[0].isalpha() or name[0] == "_") or not name.replace("_", "").isalnum():
        raise UsageError(f"{name!r} is not a name this language has")
    try:
        return name, Decimal(raw.strip())
    except InvalidOperation:
        raise UsageError(f"--var {name}={raw!r} is not a number") from None


def _values(pairs: list[str]) -> dict[str, Decimal]:
    values: dict[str, Decimal] = {}
    for pair in pairs:
        name, value = _definition(pair)
        if name in values:
            raise UsageError(f"--var {name} was given twice")
        values[name] = value
    return values


def _tree_payload(node: nodes.Node) -> dict[str, object]:
    if isinstance(node, Number):
        return {"kind": "number", "value": nodes.format_number(node.value)}
    if isinstance(node, Name):
        return {"kind": "name", "name": node.identifier}
    if isinstance(node, Unary):
        return {"kind": "unary", "op": node.op, "operand": _tree_payload(node.operand)}
    if isinstance(node, Binary):
        return {
            "kind": "binary",
            "op": node.op,
            "left": _tree_payload(node.left),
            "right": _tree_payload(node.right),
        }
    assert isinstance(node, Call)
    return {
        "kind": "call",
        "name": node.name,
        "args": [_tree_payload(arg) for arg in node.args],
    }


def _command_parse(args: argparse.Namespace) -> int:
    tree = parse(args.expression)
    if args.json:
        payload = {
            "source": args.expression,
            "render": tree.render(),
            "depth": depth(tree),
            "nodes": sum(1 for _ in walk(tree)),
            "tree": _tree_payload(tree),
        }
        print(json.dumps(payload, indent=2))
        return EXIT_OK
    print(f"source     {args.expression}")
    print(f"render     {tree.render()}")
    print(f"depth      {depth(tree)}")
    print(f"nodes      {sum(1 for _ in walk(tree))}")
    print("tree")
    for line in tree_lines(tree):
        print(f"  {line}")
    return EXIT_OK


def _evaluated(args: argparse.Namespace) -> tuple[nodes.Node, Decimal]:
    tree = parse(args.expression)
    exact = not args.inexact
    return tree, evaluate(tree, values=_values(args.var), exact=exact, text=args.expression)


def _command_eval(args: argparse.Namespace) -> int:
    tree, value = _evaluated(args)
    exact = not args.inexact
    if args.json:
        payload = {
            "source": args.expression,
            "render": tree.render(),
            "value": as_text(value),
            "exact": exact,
            "precision": None if exact else PRECISION,
        }
        print(json.dumps(payload, indent=2))
        return EXIT_OK
    print(f"render     {tree.render()}")
    print(f"value      {as_text(value)}")
    print(f"mode       {'exact' if exact else f'rounded to {PRECISION} digits'}")
    return EXIT_OK


def _command_explain(args: argparse.Namespace) -> int:
    tree = parse(args.expression)
    print(f"source     {args.expression}")
    print(f"render     {tree.render()}")
    print("precedence (lower binds looser)")
    for op, level in precedence_table():
        print(f"  {level}  {op}")
    print("tree")
    for line in tree_lines(tree):
        print(f"  {line}")
    try:
        value = evaluate(
            tree, values=_values(args.var), exact=not args.inexact, text=args.expression
        )
    except EvalError as error:
        print(f"value      refused: {error}")
        return EXIT_REFUSED
    print(f"value      {as_text(value)}")
    return EXIT_OK


def _command_demo(args: argparse.Namespace) -> int:
    text = render_stories()
    print(text)
    return EXIT_OK if text.endswith("hold") else EXIT_REFUSED


def _command_selftest(args: argparse.Namespace) -> int:
    from . import selftest

    report = selftest.run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_REFUSED


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog=PROGRAM, description="Parse and evaluate arithmetic.")
    root.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = root.add_subparsers(dest="command", required=True)

    parse_command = commands.add_parser("parse", help="print the tree and its canonical text")
    parse_command.add_argument("expression")
    parse_command.add_argument("--json", action="store_true")
    parse_command.set_defaults(handler=_command_parse)

    eval_command = commands.add_parser("eval", help="evaluate an expression")
    eval_command.add_argument("expression")
    eval_command.add_argument("--var", action="append", default=[], metavar="NAME=VALUE")
    eval_command.add_argument("--inexact", action="store_true", help="round instead of refusing")
    eval_command.add_argument("--json", action="store_true")
    eval_command.set_defaults(handler=_command_eval)

    explain = commands.add_parser("explain", help="show the tree, the table and the value")
    explain.add_argument("expression")
    explain.add_argument("--var", action="append", default=[], metavar="NAME=VALUE")
    explain.add_argument("--inexact", action="store_true")
    explain.set_defaults(handler=_command_explain)

    demo = commands.add_parser("demo", help="run the six stories")
    demo.set_defaults(handler=_command_demo)

    selftest = commands.add_parser("selftest", help="check the package against itself")
    selftest.set_defaults(handler=_command_selftest)
    return root


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except UsageError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except (LexError, ParseError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        caret = error.caret()
        if caret:
            print(caret, file=sys.stderr)
        return EXIT_UNUSABLE
    except EvalError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        caret = error.caret()
        if caret:
            print(caret, file=sys.stderr)
        return EXIT_REFUSED


if __name__ == "__main__":  # pragma: no cover - exercised through __main__
    raise SystemExit(main())
