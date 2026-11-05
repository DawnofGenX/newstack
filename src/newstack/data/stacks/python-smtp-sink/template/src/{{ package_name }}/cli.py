"""Run the sink, or inspect what it captured."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .mailbox import Mailbox
from .server import Sink, SinkConfig


def _serve(args: argparse.Namespace) -> int:
    config = SinkConfig(
        host=args.host,
        port=args.port,
        root=Path(args.mailbox),
        size_limit=args.size_limit,
        reject_recipients=tuple(args.reject or ()),
    )
    sink = Sink(config).start()
    print(f"listening on {config.host}:{sink.port}, storing to {config.root}", flush=True)
    try:
        sink.wait()
    finally:
        sink.stop()
        print(f"stopped after {sink.mailbox.count()} message(s)", file=sys.stderr)
    return 0


def _list(args: argparse.Namespace) -> int:
    mailbox = Mailbox(Path(args.mailbox))
    messages = mailbox.messages()
    if args.json:
        print(json.dumps([message.as_dict() for message in messages], indent=2))
        return 0
    for message in messages:
        print(f"{message.id} {message.size:>7} {message.sender} -> {','.join(message.recipients)}")
        if message.subject:
            print(f"    subject: {message.subject}")
    print(f"{len(messages)} message(s) in {mailbox.root}")
    return 0


def _rebuild(args: argparse.Namespace) -> int:
    mailbox = Mailbox(Path(args.mailbox))
    count = mailbox.rebuild_index()
    print(f"indexed {count} message(s) in {mailbox.root}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="{{ package_name }}")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the SMTP sink")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8025)
    serve.add_argument("--mailbox", default="mailbox")
    serve.add_argument("--size-limit", type=int, default=256 * 1024)
    serve.add_argument("--reject", action="append", default=[])
    serve.set_defaults(handler=_serve)

    listing = sub.add_parser("list", help="print what was captured")
    listing.add_argument("--mailbox", default="mailbox")
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(handler=_list)

    rebuild = sub.add_parser("rebuild", help="recreate the index from the .eml files")
    rebuild.add_argument("--mailbox", default="mailbox")
    rebuild.set_defaults(handler=_rebuild)

    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
