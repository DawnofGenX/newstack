"""Command line: list operations, call one, check a saved response.

Exit codes are part of the contract, because this is meant to run in CI:
  0  the request and the response both fit the document
  1  they do not — a documented disagreement, printed with paths
  2  the tool could not be used: bad arguments, unreadable document, dead server
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .client import Client, DriftError, TransportError
from .spec import Spec, SpecError, coerce, load

PROGRAM = "newstack-smoke-python-duckdb-report-1793898647"
DEFAULT_SPEC = "fixtures/openapi.json"

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_UNUSABLE = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Call an HTTP API through its OpenAPI document and check every answer.",
    )
    parser.add_argument(
        "--spec",
        default=DEFAULT_SPEC,
        help=f"the document to obey (default: {DEFAULT_SPEC})",
    )
    parser.add_argument("--base-url", default=None, help="override the server in the document")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="print every operation the document declares")
    commands.add_parser("selftest", help="check the checker itself")

    call = commands.add_parser("call", help="perform one operation")
    call.add_argument("operation", help="the operationId, as printed by `list`")
    call.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="a path or query parameter",
    )
    call.add_argument("--body", metavar="FILE", help="request body JSON; - reads standard input")
    call.add_argument("--json", action="store_true", help="print the response body, not a summary")
    call.add_argument("--timeout", type=float, default=10.0, help="seconds to wait for a response")

    check = commands.add_parser("validate", help="check a saved response against the document")
    check.add_argument("--operation", required=True, help="the operationId the response belongs to")
    check.add_argument(
        "--response", required=True, metavar="FILE", help="the JSON body that was received"
    )
    check.add_argument(
        "--status", type=int, default=200, help="the status it arrived with (default: 200)"
    )
    return parser


def _read_body(source: str) -> object:
    try:
        text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    except OSError as error:
        raise SpecError(f"cannot read {source}: {error.strerror}") from error
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise SpecError(f"{source}: not JSON ({error.msg} at line {error.lineno})") from error


def _params(pairs: list[str], spec: Spec, operation_id: str) -> dict[str, object]:
    operation = spec.operation(operation_id)
    values: dict[str, object] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SpecError(f"--param wants NAME=VALUE, got {pair!r}")
        name, _, raw = pair.partition("=")
        parameter = operation.parameter(name)
        if parameter is None:
            offered = ", ".join(item.name for item in operation.parameters) or "none"
            raise SpecError(f"{operation_id} takes no parameter {name!r}; it offers {offered}")
        values[name] = coerce(raw, parameter.schema)
    missing = [name for name in operation.required_parameters() if name not in values]
    if missing:
        raise SpecError(f"{operation_id} needs --param {', --param '.join(missing)}")
    return values


def _print_operations(spec: Spec) -> None:
    for operation_id in sorted(spec.operations):
        operation = spec.operations[operation_id]
        print(f"{operation_id}  {operation.method} {operation.path}")
        if operation.summary:
            print(f"    {operation.summary}")
        for parameter in operation.parameters:
            required = "required" if parameter.required else "optional"
            print(f"    {parameter.name}: {parameter.location}, {required}")


def _run(args: argparse.Namespace) -> int:
    spec = load(Path(args.spec))

    if args.command == "list":
        _print_operations(spec)
        return EXIT_OK

    client = Client(spec, base_url=args.base_url)

    if args.command == "call":
        params = _params(args.param, spec, args.operation)
        body = _read_body(args.body) if args.body else None
        reply = client.call(args.operation, params, body)
        if args.json:
            print(json.dumps(reply.body, indent=2, sort_keys=True))
        else:
            print(f"{reply.status} {reply.operation_id}  {reply.method} {reply.url}")
            print(json.dumps(reply.body, sort_keys=True))
        return EXIT_OK

    if args.command == "validate":
        operation = spec.operation(args.operation)
        body = _read_body(args.response)
        client.check(operation, f"(saved response: {args.response})", args.status, json.dumps(body))
        print(f"fits   {args.operation} at {args.status}")
        return EXIT_OK

    raise SpecError(f"unknown command {args.command!r}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "selftest":
        from .selftest import run_selftest

        return EXIT_OK if run_selftest() else EXIT_DRIFT
    try:
        return _run(args)
    except DriftError as error:
        print(f"drift  {error}", file=sys.stderr)
        for problem in error.problems:
            print(f"       {problem}", file=sys.stderr)
        return EXIT_DRIFT
    except (SpecError, TransportError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
