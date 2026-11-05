"""The command line entry point: serve, or run the self-checks."""

from __future__ import annotations

import argparse
import os
import signal
import sys
import threading

from .server import Server, parse_port

PROG = "{{ npm_name }}"
DEFAULT_PORT = "1883"


def build_parser(prog: str = PROG) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, description="An MQTT 3.1.1 broker.")
    parser.add_argument("--host", default="127.0.0.1", help="address to bind (default: 127.0.0.1)")
    parser.add_argument(
        "--port", default=os.environ.get("PORT", DEFAULT_PORT), help="TCP port to listen on"
    )
    parser.add_argument("--selftest", action="store_true", help="run the checks and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.selftest:
        from .selftest import run

        return run()
    try:
        port = parse_port(args.port)
    except ValueError as error:
        print(f"{PROG}: {error}", file=sys.stderr)
        return 2
    stopping = threading.Event()

    def on_signal(signum: int, _frame: object) -> None:
        print(f"{PROG}: signal {signum} received: draining", file=sys.stderr)
        stopping.set()

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    server = Server(args.host, port).start()
    where = f"{args.host}:{server.port}"
    print(f"{PROG}: listening on {where}", file=sys.stderr)
    try:
        while not stopping.wait(0.2):
            pass
    finally:
        server.shutdown()
    return 0
