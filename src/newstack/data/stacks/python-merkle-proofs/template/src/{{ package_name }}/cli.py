"""The command line: build a root, prove an index, or refuse a proof."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .demo import render_stories, stories
from .hashing import HashError, hex_of, unhex
from .tree import Proof, Tree, TreeError, verify

PROGRAM = "{{ npm_name }}"
VERSION = __version__

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments cannot describe a tree or a proof."""


def load_leaves(path: str) -> list[bytes]:
    """One leaf per line; a trailing newline is not a leaf."""
    handle = Path(path)
    try:
        text = handle.read_text()
    except FileNotFoundError:
        raise UsageError(f"{handle} does not exist") from None
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise UsageError(f"{handle} holds no leaves; an empty tree has nothing to prove")
    return [line.encode("utf-8") for line in lines]


def _proof_from_arguments(arguments: argparse.Namespace) -> Proof:
    if arguments.proof:
        if arguments.index is not None:
            raise UsageError(
                "--index contradicts --proof: the file already names its index, and checking "
                "a proof against a different one would silently pass"
            )
        path = Path(arguments.proof)
        try:
            payload = json.loads(path.read_text())
        except FileNotFoundError:
            raise UsageError(f"{path} does not exist") from None
        except json.JSONDecodeError as error:
            raise UsageError(f"{path} is not JSON: {error}") from None
        return Proof.from_dict(payload)
    if arguments.path is None:
        raise UsageError("verify needs --path or --proof")
    if arguments.index is None:
        raise UsageError("verify --path needs --index")
    if arguments.root is None or arguments.size is None:
        raise UsageError("verify needs --root and --size alongside --path")
    pieces = tuple(unhex(item) for item in arguments.path.split(","))
    return Proof(index=arguments.index, size=arguments.size, leaf="", path=pieces,
                 root=unhex(arguments.root))


def _command_root(arguments: argparse.Namespace) -> int:
    tree = Tree(load_leaves(arguments.leaves))
    if arguments.json:
        print(json.dumps({"size": tree.size, "root": hex_of(tree.root())}, indent=2))
    else:
        print(f"size         {tree.size}")
        print(f"root         {hex_of(tree.root())}")
    return EXIT_OK


def _command_prove(arguments: argparse.Namespace) -> int:
    tree = Tree(load_leaves(arguments.leaves))
    proof = tree.prove(arguments.index)
    if arguments.json:
        print(json.dumps(proof.as_dict(), indent=2))
    else:
        for line in proof.lines():
            print(line)
    return EXIT_OK


def _command_verify(arguments: argparse.Namespace) -> int:
    proof = _proof_from_arguments(arguments)
    verdict = verify(proof.index, arguments.leaf.encode("utf-8"), proof.path,
                     root=proof.root, size=proof.size)
    if arguments.json:
        print(json.dumps({"ok": verdict.ok, "reason": verdict.reason}, indent=2))
    else:
        print(verdict.line())
    return EXIT_OK if verdict.ok else EXIT_REFUSED


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Merkle inclusion proofs over a tree whose shape is fixed",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)

    root = commands.add_parser("root", help="print the root of a leaf file")
    root.add_argument("--leaves", required=True, help="one leaf per line")
    root.add_argument("--json", action="store_true")
    root.set_defaults(handler=_command_root)

    prove = commands.add_parser("prove", help="prove that one index is in the tree")
    prove.add_argument("--leaves", required=True)
    prove.add_argument("--index", type=int, required=True)
    prove.add_argument("--json", action="store_true")
    prove.set_defaults(handler=_command_prove)

    verifier = commands.add_parser("verify", help="check a proof from the outside")
    verifier.add_argument("--leaf", required=True, help="the leaf content")
    verifier.add_argument("--index", type=int, default=None,
                          help="required with --path; refused with --proof")
    verifier.add_argument("--size", type=int, default=None)
    verifier.add_argument("--root", default=None)
    verifier.add_argument("--path", default=None, help="comma separated sibling hashes")
    verifier.add_argument("--proof", default=None, help="JSON written by prove --json")
    verifier.add_argument("--json", action="store_true")
    verifier.set_defaults(handler=_command_verify)

    demo = commands.add_parser("demo", help="run the six stories")
    demo.set_defaults(handler=_command_demo)

    selftest = commands.add_parser("selftest", help="check the rules in-process")
    selftest.set_defaults(handler=_command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        return int(arguments.handler(arguments))
    except (UsageError, TreeError, HashError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    sys.exit(main())
