"""CLI entry point: --host/--port/--selftest, PORT env.

Run as the installed console script or `python -m {{ package_name }}`.
"""

import argparse
import os
import signal
import sys

from .server import DEFAULT_HOST, DEFAULT_PORT, serve

PROG = "{{ npm_name }}"


def _parse_port(raw: str) -> int:
    try:
        port = int(raw)
    except ValueError:
        print(f"{PROG}: invalid port {raw!r}", file=sys.stderr)
        raise SystemExit(2) from None
    if not 0 < port < 65536:
        print(f"{PROG}: invalid port {raw!r}", file=sys.stderr)
        raise SystemExit(2)
    return port


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=PROG, description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=str, default=None)
    parser.add_argument("--selftest", action="store_true", help="run socket selftest and exit")
    args = parser.parse_args(argv)

    if args.selftest:
        from .selftest import run_selftest

        return run_selftest()

    port = _parse_port(args.port or os.environ.get("PORT") or str(DEFAULT_PORT))

    def _drain(signum, _frame):
        print(f"{PROG}: signal {signum} received: draining", flush=True)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _drain)
    signal.signal(signal.SIGINT, _drain)
    serve(args.host, port)
    return 0
