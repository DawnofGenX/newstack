"""Run the authoritative server, or the checks."""

from __future__ import annotations

import argparse
import os
import signal
import sys
import threading

from .selftest import run as run_selftest
from .server import Server, parse_port
from .zone import demo_zone

PROG = "{{ npm_name }}"
DEFAULT_PORT = "5353"


def build_parser(prog: str = PROG) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog, description="An authoritative DNS server for one zone."
    )
    parser.add_argument("--host", default="127.0.0.1", help="address to bind (default: 127.0.0.1)")
    parser.add_argument(
        "--port",
        default=None,
        help=f"port to bind (default: $PORT or {DEFAULT_PORT})",
    )
    parser.add_argument("--apex", default="example.test", help="the zone apex")
    parser.add_argument("--selftest", action="store_true", help="run the checks and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        return run_selftest()

    raw_port = args.port or os.environ.get("PORT", DEFAULT_PORT)
    try:
        port = parse_port(raw_port)
    except ValueError as error:
        print(f"{PROG}: {error}", file=sys.stderr)
        return 2

    server = Server(args.host, port, zone=demo_zone(args.apex)).start()
    stopping = threading.Event()

    def on_signal(signum: int, _frame: object) -> None:
        print(f"{PROG}: signal {signum} received: draining", file=sys.stderr)
        stopping.set()

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    where = f"{args.host}:{server.port}"
    print(f"{PROG}: listening on {where} udp+tcp for {args.apex}", file=sys.stderr)
    try:
        while not stopping.wait(0.2):
            pass
    finally:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
