"""Command line entry point: prove the cache collapses a stampede."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from collections.abc import Sequence

from . import demo, selftest
from .cache import Answer, SingleFlight
from .model import LoadError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_PROBLEM = 1
EXIT_UNUSABLE = 2


def _burst(cache: SingleFlight, callers: int) -> tuple[list[Answer], list[str]]:
    answers: list[Answer] = []
    errors: list[str] = []
    gate = threading.Barrier(callers + 1)
    lock = threading.Lock()

    def worker() -> None:
        gate.wait()
        try:
            answer = cache.get("popular")
        except BaseException as error:
            with lock:
                errors.append(demo.error_of(error))
        else:
            with lock:
                answers.append(answer)

    threads = [threading.Thread(target=worker) for _ in range(callers)]
    for thread in threads:
        thread.start()
    gate.wait()
    for thread in threads:
        thread.join()
    return answers, errors


def command_run(_: argparse.Namespace, args: argparse.Namespace) -> int:
    def loader(_key: str) -> str:
        time.sleep(args.delay)
        return "expensive value"

    cache = SingleFlight(loader, ttl_s=args.ttl)
    started = time.perf_counter()
    answers, errors = _burst(cache, args.callers)
    elapsed = time.perf_counter() - started
    stats = cache.stats
    if args.json:
        print(
            json.dumps(
                {
                    "callers": args.callers,
                    "delay_s": args.delay,
                    "wall_ms": round(elapsed * 1000, 1),
                    "stats": stats.as_dict(),
                    "answers": len(answers),
                    "errors": errors,
                },
                indent=2,
            )
        )
    else:
        print(f"callers  {args.callers}, loader delay {args.delay:g}s")
        print(f"stats    {stats.line()}")
        print(f"wall     {elapsed * 1000:.0f} ms; {args.callers} sequential loads "
              f"would cost {args.callers * args.delay * 1000:.0f} ms")
        print(f"values   {len({answer.value for answer in answers})} distinct")
        for error in errors:
            print(f"error    {error}")
    return EXIT_PROBLEM if stats.loads != 1 else EXIT_OK


def command_demo(_: argparse.Namespace, args: argparse.Namespace) -> int:
    steps = demo.run()
    print(demo.render(steps) if not args.json else json.dumps(demo.payload(steps), indent=2))
    return EXIT_OK if all(step.ok for step in steps) else EXIT_PROBLEM


def command_selftest(_: argparse.Namespace, args: argparse.Namespace) -> int:
    passed, total = selftest.run()
    print(f"selftest: {passed} checks passed, {total - passed} failed out of {total}")
    return EXIT_OK if passed == total else EXIT_PROBLEM


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="One loader run per key, never one per caller."
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    runner = subparsers.add_parser("run", help="fire N callers at one cold key")
    runner.add_argument("--callers", type=int, default=50)
    runner.add_argument("--delay", type=float, default=0.1, help="loader work, in seconds")
    runner.add_argument("--ttl", type=float, default=None)
    runner.add_argument("--json", action="store_true")
    runner.set_defaults(handler=command_run)

    shower = subparsers.add_parser("demo", help="four scenarios about stampedes")
    shower.add_argument("--json", action="store_true")
    shower.set_defaults(handler=command_demo)

    tester = subparsers.add_parser("selftest", help="check the cache without pytest")
    tester.set_defaults(handler=command_selftest)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(None, args))
    except (LoadError, ValueError, TypeError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
