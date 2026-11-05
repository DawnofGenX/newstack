"""The console script: show, get, check. Exit 0 ok, 1 gate, 2 unusable."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import resolve as resolver
from . import selftest
from .spec import ConfigError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_DEFAULT_SECRET = 1
EXIT_UNUSABLE = 2
DEFAULT_PREFIX = "APP"
NAME_WIDTH = 26
VALUE_WIDTH = 34


def render(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, list | tuple):
        return "[" + ", ".join(value) + "]"
    return str(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Resolve layered configuration and report where every value came from.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="PATH",
        help="a TOML file to read before the environment",
    )
    common.add_argument("--env-prefix", default=DEFAULT_PREFIX, metavar="PREFIX")
    common.add_argument(
        "--set",
        action="append",
        default=[],
        dest="overrides",
        metavar="KEY=VALUE",
        help="highest-precedence override, repeatable",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    show = commands.add_parser(
        "show", parents=[common], help="print each setting, value and source"
    )
    show.add_argument("--json", action="store_true")
    show.add_argument(
        "--changed", action="store_true", help="only settings that did not come from the schema"
    )
    show.add_argument("--reveal", action="store_true", help="print secret values instead of ***")

    get = commands.add_parser("get", parents=[common], help="print one setting, raw")
    get.add_argument("key")
    get.add_argument("--reveal", action="store_true")

    check = commands.add_parser("check", parents=[common], help="validate the layers")
    check.add_argument(
        "--strict", action="store_true", help="exit 1 when a secret is still the schema default"
    )
    check.add_argument("--json", action="store_true")

    commands.add_parser("selftest", help="run the offline checks")
    return parser


def resolve_from(args: argparse.Namespace) -> resolver.Resolution:
    return resolver.resolve(config=args.config, flags=args.overrides, prefix=args.env_prefix)


def report_problems(problems: tuple[str, ...]) -> None:
    for problem in problems:
        print(f"problem  {problem}", file=sys.stderr)


def payload(resolution: resolver.Resolution, chosen: list[resolver.Value], reveal: bool) -> dict:
    return {
        "ok": resolution.ok,
        "problems": list(resolution.problems),
        "values": {
            value.key.name: {
                "value": value.shown(reveal),
                "source": value.source,
                "origin": value.origin,
            }
            for value in chosen
        },
    }


def cmd_show(args: argparse.Namespace) -> int:
    resolution = resolve_from(args)
    chosen = resolution.changed() if args.changed else list(resolution.values.values())
    if args.json:
        print(json.dumps(payload(resolution, chosen, args.reveal), indent=2))
        return EXIT_OK if resolution.ok else EXIT_UNUSABLE
    for value in chosen:
        shown = render(value.shown(args.reveal))
        print(f"{value.key.name:<{NAME_WIDTH}} {shown:<{VALUE_WIDTH}} {value.source}")
    if not chosen:
        print("(nothing differs from the schema defaults)")
    report_problems(resolution.problems)
    return EXIT_OK if resolution.ok else EXIT_UNUSABLE


def cmd_get(args: argparse.Namespace) -> int:
    resolution = resolve_from(args)
    if not resolution.ok:
        report_problems(resolution.problems)
        return EXIT_UNUSABLE
    try:
        value = resolution.get(args.key)
    except ConfigError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    if value.key.secret and not args.reveal:
        print(f"{PROGRAM}: {args.key} is a secret; pass --reveal to print it", file=sys.stderr)
        return EXIT_UNUSABLE
    print(render(value.value))
    return EXIT_OK


def cmd_check(args: argparse.Namespace) -> int:
    resolution = resolve_from(args)
    default_secrets = resolution.default_secrets()
    if args.json:
        print(
            json.dumps(
                {
                    "ok": resolution.ok,
                    "settings": len(resolution.values),
                    "changed": len(resolution.changed()),
                    "problems": list(resolution.problems),
                    "default_secrets": [value.key.name for value in default_secrets],
                },
                indent=2,
            )
        )
        if not resolution.ok:
            return EXIT_UNUSABLE
        return EXIT_DEFAULT_SECRET if args.strict and default_secrets else EXIT_OK
    if resolution.problems:
        report_problems(resolution.problems)
        print(f"check  FAILED: {len(resolution.problems)} problem(s)", file=sys.stderr)
        return EXIT_UNUSABLE
    changed = len(resolution.changed())
    at_default = len(resolution.values) - changed
    counted = f"check  ok: {len(resolution.values)} settings, {changed} from a layer"
    print(f"{counted}, {at_default} at their default")
    if args.strict:
        if default_secrets:
            for value in default_secrets:
                shown = render(value.key.default)
                print(
                    f"gate   {value.key.name} is still the schema default ({shown}) — "
                    "a secret that ships with the code is not a secret",
                    file=sys.stderr,
                )
            return EXIT_DEFAULT_SECRET
        print("gate   no secret is at its default")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "selftest":
        return selftest.main()
    handlers = {"show": cmd_show, "get": cmd_get, "check": cmd_check}
    try:
        return handlers[args.command](args)
    except ConfigError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
