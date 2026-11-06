"""The command line: sign a request, or explain why a signature is refused."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import __version__
from .canonical import CanonicalError
from .demo import render_stories, stories
from .sign import (
    DEFAULT_TTL_S,
    Signature,
    SignatureError,
    Verifier,
    sign,
    signing_string,
)

PROGRAM = "{{ npm_name }}"
VERSION = __version__

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments cannot describe a request."""


def _headers(values: list[str] | None) -> dict[str, str]:
    header_map: dict[str, str] = {}
    for item in values or []:
        name, separator, value = item.partition(":")
        if not separator or not name.strip():
            raise UsageError(f"--header wants name:value, not '{item}'")
        header_map[name.strip().lower()] = value.strip()
    return header_map


def _body(text: str | None) -> bytes:
    return (text or "").encode("utf-8")


def _signed(names: list[str] | None) -> tuple[str, ...]:
    return tuple(sorted({name.strip().lower() for name in names or []}))


def _print_signature(signature: Signature, *, show_string: bool) -> None:
    print("request      signed")
    if show_string:
        print("signing string")
        for line in signature.canonical.split("\n"):
            print(f"  {line}")
    for line in signature.lines():
        print(line)


def _command_sign(arguments: argparse.Namespace) -> int:
    signature = sign(
        arguments.secret,
        arguments.method,
        arguments.url,
        timestamp=arguments.timestamp,
        headers=_headers(arguments.header),
        body=_body(arguments.body),
        signed_headers=_signed(arguments.signed_header),
        ttl_s=arguments.ttl,
    )
    if arguments.json:
        print(json.dumps(signature.as_dict(), indent=2))
    else:
        _print_signature(signature, show_string=arguments.show_string)
    return EXIT_OK


def _read_signature(arguments: argparse.Namespace) -> Signature:
    if arguments.signature_file:
        path = Path(arguments.signature_file)
        try:
            payload = json.loads(path.read_text())
        except FileNotFoundError:
            raise UsageError(f"{path} does not exist") from None
        except json.JSONDecodeError as error:
            raise UsageError(f"{path} is not JSON: {error}") from None
        return Signature.from_dict(payload)
    if arguments.signature is None:
        raise UsageError("verify needs --signature or --signature-file")
    return Signature(
        value=arguments.signature,
        timestamp=arguments.timestamp if arguments.timestamp is not None else arguments.now,
        expires=(arguments.expires if arguments.expires is not None
                 else (arguments.timestamp or arguments.now) + DEFAULT_TTL_S),
        signed_headers=_signed(arguments.signed_header),
        canonical="",
    )


def _command_verify(arguments: argparse.Namespace) -> int:
    signature = _read_signature(arguments)
    verifier = Verifier(arguments.secret, ttl_s=arguments.ttl)
    verdict = verifier.verify(
        arguments.method,
        arguments.url,
        signature,
        now_s=arguments.now,
        headers=_headers(arguments.header),
        body=_body(arguments.body),
    )
    if arguments.json:
        print(json.dumps({"ok": verdict.ok, "reason": verdict.reason}, indent=2))
    else:
        print(verdict.line())
    return EXIT_OK if verdict.ok else EXIT_REFUSED


def _command_string(arguments: argparse.Namespace) -> int:
    text = signing_string(
        arguments.method,
        arguments.url,
        timestamp=arguments.timestamp,
        headers=_headers(arguments.header),
        body=_body(arguments.body),
        signed_headers=_signed(arguments.signed_header),
    )
    for line in text.split("\n"):
        print(line)
    return EXIT_OK


def _command_demo(_: argparse.Namespace) -> int:
    print(render_stories())
    broken = [story.title for story in stories() if not story.held]
    if broken:
        print(f"{PROGRAM}: {len(broken)} story(ies) no longer hold:")
        for title in broken:
            print(f"  {title}")
        return EXIT_REFUSED
    return EXIT_OK


def _command_selftest(_: argparse.Namespace) -> int:
    from . import selftest

    return selftest.main()


def _add_request_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--method", default="GET", help="HTTP method (default: GET)")
    parser.add_argument("--url", required=True, help="absolute path, query included")
    parser.add_argument("--header", action="append", metavar="NAME:VALUE",
                       help="request header, repeatable")
    parser.add_argument("--signed-header", action="append", metavar="NAME",
                       help="header covered by the signature, repeatable")
    parser.add_argument("--body", default="", help="request body as text")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="sign requests over a canonical form, and explain every refusal",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)

    signer = commands.add_parser("sign", help="produce a signature")
    _add_request_options(signer)
    signer.add_argument("--secret", required=True)
    signer.add_argument("--timestamp", type=int, default=None,
                        help="issue time in epoch seconds (default: now)")
    signer.add_argument("--ttl", type=int, default=DEFAULT_TTL_S)
    signer.add_argument("--json", action="store_true")
    signer.add_argument("--show-string", action="store_true",
                        help="print the exact text the HMAC covers")
    signer.set_defaults(handler=_command_sign)

    verifier = commands.add_parser("verify", help="check a signature")
    _add_request_options(verifier)
    verifier.add_argument("--secret", required=True)
    verifier.add_argument("--signature", help="the hex signature")
    verifier.add_argument("--signature-file", help="JSON written by sign --json")
    verifier.add_argument("--timestamp", type=int, default=None)
    verifier.add_argument("--expires", type=int, default=None)
    verifier.add_argument("--now", type=int, default=None, help="current epoch seconds")
    verifier.add_argument("--ttl", type=int, default=DEFAULT_TTL_S)
    verifier.add_argument("--json", action="store_true")
    verifier.set_defaults(handler=_command_verify)

    stringer = commands.add_parser("string", help="print the signing string only")
    _add_request_options(stringer)
    stringer.add_argument("--timestamp", type=int, default=None)
    stringer.set_defaults(handler=_command_string)

    demo = commands.add_parser("demo", help="run the six stories")
    demo.set_defaults(handler=_command_demo)

    selftest = commands.add_parser("selftest", help="check the rules in-process")
    selftest.set_defaults(handler=_command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if getattr(arguments, "timestamp", None) is None and hasattr(arguments, "timestamp"):
        arguments.timestamp = int(time.time())
    if getattr(arguments, "now", None) is None and hasattr(arguments, "now"):
        arguments.now = int(time.time())
    try:
        return int(arguments.handler(arguments))
    except (UsageError, SignatureError, CanonicalError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    sys.exit(main())
