"""Command line: sanitize a file, check a corpus, or watch the demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import demo
from .audit import audit
from .errors import PolicyError, SanitizeError
from .policy import DEFAULT, DROP_CONTENT, VOID_TAGS
from .sanitize import explain

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_PROBLEM = 1
EXIT_UNUSABLE = 2


def read_text(path: str) -> str:
    """Bytes, then decode: text mode would normalise line endings in the input."""
    if path == "-":
        data = sys.stdin.buffer.read()
        name = "stdin"
    else:
        try:
            data = Path(path).read_bytes()
        except OSError as error:
            raise SanitizeError(f"cannot read {path}: {error.strerror or error}") from error
        name = path
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SanitizeError(f"{name} is not UTF-8: {error}") from error


def command_render(args: argparse.Namespace) -> int:
    output, stats = explain(read_text(args.file), args.policy)
    if args.json:
        print(json.dumps({"output": output, "stats": stats.as_dict()}, indent=2, sort_keys=True))
        return EXIT_OK
    print(output)
    print(stats.line(), file=sys.stderr)
    return EXIT_OK


def command_check(args: argparse.Namespace) -> int:
    failures = 0
    rows = []
    for path in args.files:
        text = read_text(path)
        verdict = audit(text, args.policy)
        rows.append({"path": path, **verdict.as_dict()})
        if verdict.ok:
            print(f"ok       {path}")
        else:
            failures += 1
            print(f"FAIL     {path}")
            for problem in verdict.problems:
                print(f"         {problem}")
            if not verdict.idempotent:
                print("         a second pass over the output changes it")
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    return EXIT_PROBLEM if failures else EXIT_OK


def command_policy(args: argparse.Namespace) -> int:
    policy = args.policy
    print(f"tags     {' '.join(sorted(policy.allowed_tags))}")
    for tag in sorted(policy.allowed_attributes):
        print(f"attrs    {tag}: {' '.join(sorted(policy.allowed_attributes[tag]))}")
    print(f"schemes  {' '.join(sorted(policy.allowed_schemes))}")
    print(f"comments {'allowed' if policy.allow_comments else 'dropped'}")
    print(f"content  always dropped inside: {' '.join(sorted(DROP_CONTENT))}")
    print(f"void     never closed: {' '.join(sorted(VOID_TAGS))}")
    return EXIT_OK


def command_demo(_args: argparse.Namespace) -> int:
    steps = demo.run()
    print("\n".join(demo.render(steps)))
    return EXIT_OK if all(step.ok for step in steps) else EXIT_PROBLEM


def command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="Sanitize HTML by rebuilding it from an allowlist."
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command")

    def add(name: str, handler, help_text: str) -> argparse.ArgumentParser:
        child = commands.add_parser(name, help=help_text)
        child.set_defaults(handler=handler, policy=DEFAULT)
        return child

    render = add("render", command_render, "sanitize a file (or - for stdin)")
    render.add_argument("--file", default="-", help="file to sanitize, - for stdin")
    render.add_argument(
        "--json", action="store_true", help="print the output and the counters as JSON"
    )

    check = add("check", command_check, "audit files: nothing dangerous, and a fixed point")
    check.add_argument("files", nargs="+")
    check.add_argument("--json", action="store_true", help="print the verdicts as JSON")

    add("policy", command_policy, "print the allowlist in use")
    add("demo", command_demo, "run the eight vectors")
    add("selftest", command_selftest, "run the checks without the prose")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "handler", None) is None:
        parser.print_help(sys.stderr)
        return EXIT_UNUSABLE
    try:
        return int(args.handler(args))
    except (SanitizeError, PolicyError, ValueError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
