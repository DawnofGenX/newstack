"""Command line entry point: `run` a batch, resume it, and report counts.

Exit codes are part of the contract: 0 everything answered, 1 something failed
permanently (the results file still holds every answer), 2 the batch could not
be read or written at all.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from {{ package_name }} import __version__
from {{ package_name }}.client import ChatClient
from {{ package_name }}.records import (
    RecordError,
    Request,
    ResultWriter,
    load_requests,
    load_results,
    parse_requests,
)
from {{ package_name }}.runner import run

EXIT_OK = 0
EXIT_FAILURES = 1
EXIT_UNUSABLE = 2


def build_parser() -> argparse.ArgumentParser:
    """The CLI surface, described in one place so `--help` and tests agree."""
    parser = argparse.ArgumentParser(
        prog="{{ npm_name }}",
        description="Resumable batch inference against an OpenAI-compatible endpoint.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="send every request and append the results")
    run_parser.add_argument("--requests", required=True, help="JSONL file, or - for stdin")
    run_parser.add_argument("--out", required=True, help="JSONL results file, appended to")
    run_parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:5468/v1",
        help="OpenAI-compatible base URL (default: %(default)s)",
    )
    run_parser.add_argument("--model", default="stub-model")
    run_parser.add_argument("--concurrency", type=int, default=4)
    run_parser.add_argument("--max-attempts", type=int, default=4)
    run_parser.add_argument("--timeout", type=float, default=10.0)
    run_parser.add_argument("--backoff", type=float, default=0.05)
    run_parser.add_argument("--limit", type=int, default=0, help="only the first N pending")
    run_parser.add_argument(
        "--no-resume",
        action="store_true",
        help="ignore ids already present in --out and send them again",
    )
    sub.add_parser("selftest", help="run the offline checks and exit non-zero on a failure")
    return parser


def _requests(args: argparse.Namespace) -> list[Request]:
    if args.requests == "-":
        return parse_requests(sys.stdin, "<stdin>")
    return load_requests(args.requests)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse, run, report. Never raises for a bad batch — it exits 2 instead."""
    args = build_parser().parse_args(argv)
    if args.command == "selftest":
        from {{ package_name }}.selftest import run as selftest

        return selftest()
    try:
        requests = _requests(args)
        done = {} if args.no_resume else load_results(args.out)
    except RecordError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE

    pending = [request for request in requests if request.id not in done]
    if args.limit > 0:
        pending = pending[: args.limit]
    resumed = len(requests) - len(pending)

    client = ChatClient(
        args.base_url,
        model=args.model,
        timeout=args.timeout,
        max_attempts=args.max_attempts,
        backoff=args.backoff,
    )
    try:
        with ResultWriter(args.out) as writer:
            summary = run(
                pending,
                client,
                writer,
                concurrency=args.concurrency,
                total=len(requests),
                resumed=resumed,
            )
    except OSError as exc:
        print(f"error: {args.out}: cannot write ({exc.strerror})", file=sys.stderr)
        return EXIT_UNUSABLE

    for line in summary.lines():
        print(line)
    return EXIT_FAILURES if summary.failed else EXIT_OK
