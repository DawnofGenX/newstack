"""Serve, or run the self-checks."""

from __future__ import annotations

import argparse
import os
import signal
import sys
import threading

from .selftest import run as run_selftest
from .server import Server, parse_port

PROG = "{{ npm_name }}"


def build_parser(prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, description="A small RESP2 key-value server.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", default=os.environ.get("PORT", "6380"))
    parser.add_argument(
        "--idle", type=float, default=30.0, help="seconds before an idle client is dropped"
    )
    parser.add_argument("--selftest", action="store_true", help="run the checks and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser(PROG)
    options = parser.parse_args(argv)
    if options.selftest:
        return run_selftest()
    try:
        port = parse_port(str(options.port))
    except ValueError as exc:
        print(f"{PROG}: {exc}", file=sys.stderr)
        return 2

    server = Server(options.host, port, idle=options.idle).start()
    stopping = threading.Event()

    def drain(signum, frame) -> None:
        print(f"{PROG}: signal {signum} received: draining", file=sys.stderr, flush=True)
        stopping.set()

    signal.signal(signal.SIGTERM, drain)
    signal.signal(signal.SIGINT, drain)
    print(f"{PROG}: listening on {options.host}:{server.port}", flush=True)
    try:
        stopping.wait()
    finally:
        server.shutdown()
    return 0
