"""The command line: one request, one answer, and the effect count behind it."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from . import demo, guard, model
from .store import Store

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_UNUSABLE = 2
DEFAULT_DB = Path("idempotency.db")
DEFAULT_SCOPE = "charge"


def _charge(request: model.Request) -> model.Response:
    amount = request.body.get("amount", 0)
    return model.Response(status=201, body=json.dumps({"charged": amount}, sort_keys=True))


def _fail(request: model.Request) -> model.Response:
    raise RuntimeError("the provider refused the charge")


def _slow(request: model.Request) -> model.Response:
    time.sleep(0.2)
    return _charge(request)


HANDLERS = {"charge": _charge, "fail": _fail, "slow": _slow}


def _body(text: str) -> dict:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise model.InputError(f"--body is not JSON: {error}") from error
    if not isinstance(payload, dict):
        raise model.InputError(f"--body must be a JSON object, got {type(payload).__name__}")
    return payload


def command_request(store: Store | None, args: argparse.Namespace) -> int:
    assert store is not None
    request = model.Request(scope=args.scope, key=args.key, body=_body(args.body))
    handler = HANDLERS[args.handler]
    try:
        outcome = guard.execute(store, request, handler, lease_s=args.lease)
    except model.InProgress as error:
        print(f"in flight  {error}", file=sys.stderr)
        return EXIT_REFUSED
    except model.Mismatch as error:
        print(f"mismatch   {error}", file=sys.stderr)
        return EXIT_REFUSED
    if args.json:
        print(
            json.dumps(
                {
                    "key": outcome.key,
                    "status": outcome.status,
                    "body": outcome.body,
                    "replay": outcome.replay,
                    "attempts": outcome.attempts,
                },
                sort_keys=True,
            )
        )
    else:
        print(outcome.line())
    return EXIT_OK


def command_show(store: Store | None, args: argparse.Namespace) -> int:
    assert store is not None
    row = store.get(args.scope, args.key)
    if row is None:
        print(f"{PROGRAM}: no key {args.key!r} in {args.scope}", file=sys.stderr)
        return EXIT_UNUSABLE
    for name, value in zip(row.keys(), tuple(row), strict=True):
        print(f"{name:<12} {value}")
    return EXIT_OK


def command_demo(store: Store | None, args: argparse.Namespace) -> int:
    del store, args
    steps = demo.run(Path("demo-work"))
    print(demo.render(steps))
    return EXIT_OK if all(step.ok for step in steps) else EXIT_REFUSED


def command_selftest(store: Store | None, args: argparse.Namespace) -> int:
    del store, args
    from . import selftest

    passed, failed, total = selftest.run()
    print(f"selftest: {passed} checks passed, {failed} failed out of {total}")
    return EXIT_OK if failed == 0 else EXIT_REFUSED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="Idempotency keys: one effect per key, replays on retry."
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="key table")
    subparsers = parser.add_subparsers(dest="command", required=True)

    request = subparsers.add_parser("request", help="run one request under a key")
    request.add_argument("--key", required=True)
    request.add_argument("--scope", default=DEFAULT_SCOPE)
    request.add_argument("--body", default="{}")
    request.add_argument("--handler", choices=sorted(HANDLERS), default="charge")
    request.add_argument("--lease", type=float, default=None)
    request.add_argument("--json", action="store_true")
    request.set_defaults(handler_function=command_request)

    show = subparsers.add_parser("show", help="print the stored row for a key")
    show.add_argument("--key", required=True)
    show.add_argument("--scope", default=DEFAULT_SCOPE)
    show.set_defaults(handler_function=command_show)

    subparsers.add_parser("demo", help="prove the four scenarios").set_defaults(
        handler_function=command_demo
    )
    subparsers.add_parser("selftest", help="check the library").set_defaults(
        handler_function=command_selftest
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    function = args.handler_function
    if function in (command_demo, command_selftest):
        return int(function(None, args))
    try:
        with Store(args.db) as store:
            return int(function(store, args))
    except (model.InputError, ValueError, OSError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except RuntimeError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
