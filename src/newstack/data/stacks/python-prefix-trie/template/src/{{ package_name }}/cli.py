"""The command line: one question per run, and words in lexicographic order."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_words
from .demo import stories
from .trie import PrefixTrie, TrieError
from .words import WordError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _trie(args: argparse.Namespace) -> PrefixTrie:
    return PrefixTrie(load_words(args.words))


def _payload(trie: PrefixTrie, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "words": len(trie),
        "corpus": trie.walk(),
    }
    payload.update(extra)
    return payload


def _render(words: list[str]) -> list[str]:
    return [f"  {word}" for word in words]


def _command_add(args: argparse.Namespace) -> int:
    trie = _trie(args)
    added = sum(trie.insert(word) for word in args.new_words)
    if args.json:
        payload = _payload(trie, {"added": added})
        print(json.dumps(payload, indent=2))
    else:
        print(f"words      {len(trie)} held, {added} added")
        for word in args.new_words:
            print(f"  {word}      {'stored' if trie.has(word) else 'refused'}")
    return EXIT_OK


def _command_has(args: argparse.Namespace) -> int:
    trie = _trie(args)
    found = all(trie.has(word) for word in args.asked)
    if args.json:
        payload = _payload(trie, {"asked": args.asked, "held": found})
        print(json.dumps(payload, indent=2))
    else:
        for word in args.asked:
            print(f"{word:<16} {'word' if trie.has(word) else 'not a word'}")
    return EXIT_OK if found else EXIT_MISS


def _command_prefix(args: argparse.Namespace) -> int:
    trie = _trie(args)
    found = trie.prefix(args.prefix)
    if args.json:
        payload = _payload(trie, {"stem": args.prefix, "count": len(found),
                                  "listing": found})
        print(json.dumps(payload, indent=2))
    else:
        print(f"stem       {args.prefix!r}")
        print(f"under      {len(found)} word(s)")
        for line in _render(found):
            print(line)
    return EXIT_OK if found else EXIT_MISS


def _command_delete(args: argparse.Namespace) -> int:
    trie = _trie(args)
    dropped = trie.delete(args.word)
    if args.json:
        payload = _payload(trie, {"word": args.word, "deleted": dropped})
        print(json.dumps(payload, indent=2))
    else:
        print(f"word       {args.word!r}")
        print(f"deleted    {dropped}, {len(trie)} remain")
    return EXIT_OK if dropped else EXIT_MISS


def _command_count(args: argparse.Namespace) -> int:
    trie = _trie(args)
    if args.json:
        print(json.dumps(_payload(trie, {}), indent=2))
    else:
        print(f"words      {len(trie)} held")
        print(f"prefix     {trie.longest_common_prefix()!r} shared by all")
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_MISS


def _command_demo(_args: argparse.Namespace) -> int:
    told = stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_MISS


def _corpus_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--words", required=True, help="one word per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A string-keyed trie over lowercase words: add, has, "
        "prefix, delete, count.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="store words in the trie")
    _corpus_args(add_parser)
    add_parser.add_argument("new_words", nargs="+", metavar="WORD")
    add_parser.add_argument("--json", action="store_true")
    add_parser.set_defaults(handler=_command_add)

    has_parser = subparsers.add_parser("has", help="membership, exactly")
    _corpus_args(has_parser)
    has_parser.add_argument("asked", nargs="+", metavar="WORD")
    has_parser.add_argument("--json", action="store_true")
    has_parser.set_defaults(handler=_command_has)

    prefix_parser = subparsers.add_parser(
        "prefix", help="every word under a stem, in order"
    )
    _corpus_args(prefix_parser)
    prefix_parser.add_argument("--prefix", default="", metavar="STEM")
    prefix_parser.add_argument("--json", action="store_true")
    prefix_parser.set_defaults(handler=_command_prefix)

    delete_parser = subparsers.add_parser("delete", help="drop one exact word")
    _corpus_args(delete_parser)
    delete_parser.add_argument("word", metavar="WORD")
    delete_parser.add_argument("--json", action="store_true")
    delete_parser.set_defaults(handler=_command_delete)

    count_parser = subparsers.add_parser("count", help="size and shared stem")
    _corpus_args(count_parser)
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

    selftest_parser = subparsers.add_parser("selftest", help="the invariants")
    selftest_parser.set_defaults(handler=_command_selftest)

    demo_parser = subparsers.add_parser("demo", help="six stories, computed live")
    demo_parser.set_defaults(handler=_command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (CorpusError, WordError, TrieError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
