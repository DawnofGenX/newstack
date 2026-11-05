"""Command line: place keys, move a node in, and gate on what moved."""

from __future__ import annotations

import argparse
import json
import sys

from .audit import histogram, mod_map, moved, percentage
from .demo import render
from .ring import DEFAULT_VNODES, Ring, RingError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BREACH = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The command line does not describe a ring we can build."""


def _nodes(text: str) -> list[str]:
    nodes = [part.strip() for part in text.split(",") if part.strip()]
    if not nodes:
        raise UsageError("--nodes needs at least one name")
    duplicates = {node for node in nodes if nodes.count(node) > 1}
    if duplicates:
        raise UsageError(f"--nodes repeats {sorted(duplicates)}")
    return nodes


def _keys(count: int) -> list[str]:
    if count < 1:
        raise UsageError("--keys must be at least 1")
    return [f"key:{number:06d}" for number in range(count)]


def _ring(nodes: list[str], vnodes: int) -> Ring:
    ring = Ring(vnodes=vnodes)
    for node in nodes:
        ring.add(node)
    return ring


def _weights(text: str | None) -> dict[str, int]:
    if not text:
        return {}
    weights: dict[str, int] = {}
    for part in text.split(","):
        name, _, value = part.partition("=")
        name = name.strip()
        if not name or not value.strip().isdigit():
            raise UsageError(f"--weights expects name=count, got {part!r}")
        weights[name] = int(value)
    return weights


def command_map(args: argparse.Namespace) -> int:
    keys = _keys(args.keys)
    ring = _ring(_nodes(args.nodes), args.vnodes)
    loads = ring.loads(keys)
    imbalance = ring.imbalance(keys)
    table = "\n".join(f"{node:<12} {load:>7}" for node, load in loads.items())
    print(f"nodes      {len(ring.nodes)}")
    print(f"points     {len(ring.points)}")
    print(f"vnodes     {ring.vnodes}")
    print(f"keys       {len(keys)}")
    print(table)
    print(f"imbalance  {imbalance:.2f}")
    if args.json:
        print(
            json.dumps(
                {
                    "nodes": ring.nodes,
                    "points": len(ring.points),
                    "loads": loads,
                    "imbalance": imbalance,
                },
                indent=2,
            )
        )
    return EXIT_OK


def command_ring(args: argparse.Namespace) -> int:
    if not args.key:
        raise UsageError("--key is required")
    ring = _ring(_nodes(args.nodes), args.vnodes)
    weights = _weights(args.weights)
    for node in ring.nodes:
        if node in weights:
            del weights[node]
    for node, weight in weights.items():
        ring.add(node, weight=weight)
    owner = ring.owner(args.key)
    print(f"key        {args.key}")
    print(f"hash       {owner.position}")
    print(f"owner      {owner.node}")
    print(f"points     {len(ring.points)}")
    return EXIT_OK


def command_move(args: argparse.Namespace) -> int:
    before_nodes = _nodes(args.nodes)
    added = [node.strip() for node in args.add.split(",") if node.strip()]
    if not added:
        raise UsageError("--add needs at least one name")
    overlap = sorted(set(added) & set(before_nodes))
    if overlap:
        raise UsageError(f"--add names nodes already on the ring: {overlap}")
    keys = _keys(args.keys)
    before_ring = _ring(before_nodes, args.vnodes)
    after_ring = _ring([*before_nodes, *added], args.vnodes)
    before = before_ring.mapping(keys)
    after = after_ring.mapping(keys)
    changes = moved(before, after)
    share = percentage(len(changes), len(keys))
    after_nodes = before_ring.nodes + added
    fair = percentage(len(added), len(after_nodes))
    limit = args.max_moved if args.max_moved is not None else fair * args.tolerance
    strangers = [change for change in changes if change.after not in added]
    print(f"nodes        {len(before_nodes)} -> {len(after_nodes)}")
    print(f"added        {', '.join(added)}")
    print(f"moved        {len(changes)} of {len(keys)} ({share:.1f}%)")
    print(f"fair share   {fair:.1f}%")
    print(f"limit        {limit:.1f}%")
    naive = percentage(
        len(moved(mod_map(keys, before_nodes), mod_map(keys, after_nodes))), len(keys)
    )
    print(f"modulo       {naive:.1f}% would have moved")
    print(f"strangers    {len(strangers)} (keys that moved to a node that was already there)")
    if args.show:
        for change in changes[: args.show]:
            print(f"  {change.line()}")
    if strangers:
        print(f"gate         FAIL: {len(strangers)} key(s) moved to an old node")
        return EXIT_BREACH
    if share > limit:
        print(f"gate         FAIL: {share:.1f}% moved, limit {limit:.1f}%")
        return EXIT_BREACH
    print(f"gate         ok ({share:.1f}% <= {limit:.1f}%)")
    return EXIT_OK


def command_balance(args: argparse.Namespace) -> int:
    keys = _keys(args.keys)
    ring = _ring(_nodes(args.nodes), args.vnodes)
    loads = ring.loads(keys)
    imbalance = ring.imbalance(keys)
    total = sum(loads.values())
    print(f"vnodes      {ring.vnodes}")
    for node, load in loads.items():
        print(f"  {node:<12} {load:>7}  {percentage(load, total):5.1f}%")
    print(f"histogram   {' '.join(f'{n}={c}' for n, c in histogram(ring.mapping(keys)).items())}")
    print(f"imbalance   {imbalance:.2f} (largest share / smallest)")
    if imbalance > args.max_imbalance:
        print(f"gate        FAIL: {imbalance:.2f} > {args.max_imbalance:.2f}")
        return EXIT_BREACH
    print(f"gate        ok ({imbalance:.2f} <= {args.max_imbalance:.2f})")
    return EXIT_OK


def command_demo(args: argparse.Namespace) -> int:
    sys.stdout.write(render())
    return EXIT_OK


def command_selftest(args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="a consistent hash ring you can audit"
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--nodes", default="alpha,bravo,charlie")
    common.add_argument("--vnodes", type=int, default=DEFAULT_VNODES)
    common.add_argument("--keys", type=int, default=1000)

    mapping = sub.add_parser("map", parents=[common], help="place keys and print the loads")
    mapping.add_argument("--json", action="store_true")
    mapping.set_defaults(func=command_map)

    ring = sub.add_parser("ring", parents=[common], help="say which node owns one key")
    ring.add_argument("--key", required=True)
    ring.add_argument("--weights", default=None, help="name=count,name=count")
    ring.set_defaults(func=command_ring)

    moving = sub.add_parser("move", parents=[common], help="add nodes and audit what moved")
    moving.add_argument("--add", required=True)
    moving.add_argument(
        "--max-moved",
        type=float,
        default=None,
        help="percentage limit, default 1.5x the fair share",
    )
    moving.add_argument("--tolerance", type=float, default=1.5)
    moving.add_argument("--show", type=int, default=0)
    moving.set_defaults(func=command_move)

    balance = sub.add_parser("balance", parents=[common], help="gate on how even the split is")
    balance.add_argument("--max-imbalance", type=float, default=1.5)
    balance.set_defaults(func=command_balance)

    demo = sub.add_parser("demo", help="six stories")
    demo.set_defaults(func=command_demo)
    selftest = sub.add_parser("selftest", help="check the invariants")
    selftest.set_defaults(func=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except (UsageError, RingError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
