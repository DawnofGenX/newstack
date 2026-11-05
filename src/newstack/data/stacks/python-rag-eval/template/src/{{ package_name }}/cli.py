"""The command line: evaluate, search, compare, and check itself."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .chunk import DEFAULT_OVERLAP, DEFAULT_SIZE, chunk_corpus
from .evaluate import Report, evaluate
from .index import BM25
from .qrels import InputError, check_documents_exist, load_corpus, load_qrels

PROGRAM = "{{ npm_name }}"
DEFAULT_CORPUS = Path("fixtures/corpus")
DEFAULT_QRELS = Path("fixtures/qrels.json")

EXIT_OK = 0
EXIT_REGRESSION = 1
EXIT_UNUSABLE = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Evaluate retrieval against labelled queries, offline and deterministically.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {__version__}")

    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("eval", help="score every judged query")
    run.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    run.add_argument("--qrels", type=Path, default=DEFAULT_QRELS)
    run.add_argument("--k", type=int, default=None, help="cut-off (default: the file's k)")
    run.add_argument("--size", type=int, default=DEFAULT_SIZE, help="words per chunk")
    run.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP, help="words shared")
    run.add_argument("--json", action="store_true", help="print the report as JSON")

    search = commands.add_parser("search", help="show the ranked documents for one query")
    search.add_argument("query")
    search.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    search.add_argument("--k", type=int, default=5)
    search.add_argument("--size", type=int, default=DEFAULT_SIZE)
    search.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP)

    compare = commands.add_parser("compare", help="gate a change against a saved report")
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--candidate", type=Path, required=True)
    compare.add_argument(
        "--tolerance",
        type=float,
        default=0.0,
        help="an allowed drop, e.g. 0.01 (default: 0.0)",
    )

    commands.add_parser("selftest", help="check the checker")
    return parser


def _print_report(report: Report) -> None:
    total = len(report.scores)
    print(
        f"report {total} queries, {report.judged} judged, {report.skipped} skipped"
    )
    print(f"chunks {report.chunks} (size {report.size}, overlap {report.overlap})")
    for score in report.scores:
        if score.relevant == 0:
            print(f"skip   no judgements   {score.query}")
            continue
        print(
            f"recall@{report.k} {score.recall:.2f}  ndcg {score.ndcg:.2f}  "
            f"rr {score.reciprocal_rank:.2f}  {score.top}  {score.query}"
        )
    print(
        f"macro  recall@{report.k} {report.macro('recall'):.2f}  "
        f"precision {report.macro('precision'):.2f}  ndcg {report.macro('ndcg'):.2f}  "
        f"mrr {report.macro('reciprocal_rank'):.2f}"
    )
    print(f"micro  recall@{report.k} {report.micro_recall:.2f}")


def _run_eval(args: argparse.Namespace) -> int:
    corpus = load_corpus(args.corpus)
    qrels = load_qrels(args.qrels)
    check_documents_exist(corpus, qrels)
    k = args.k if args.k is not None else qrels.k
    report = evaluate(corpus, qrels.queries, size=args.size, overlap=args.overlap, k=k)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        _print_report(report)
    return EXIT_OK


def _run_search(args: argparse.Namespace) -> int:
    corpus = load_corpus(args.corpus)
    chunks = chunk_corpus(corpus, size=args.size, overlap=args.overlap)
    index = BM25(chunks)
    hits = index.search(args.query, k=args.k)
    if not hits:
        print("no chunk shares a word with that query", file=sys.stderr)
        return EXIT_REGRESSION
    for position, hit in enumerate(hits, start=1):
        print(f"{position:2d} {hit.score:6.3f} {hit.chunk_id:24s} {hit.doc_id}")
    return EXIT_OK


def _load_report(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InputError(f"report not found: {path}") from error
    except json.JSONDecodeError as error:
        raise InputError(f"{path}: not JSON ({error.msg})") from error
    if not isinstance(loaded, dict) or "macro_recall" not in loaded:
        raise InputError(f"{path}: not a report produced by this tool")
    return loaded


def _run_compare(args: argparse.Namespace) -> int:
    baseline = _load_report(args.baseline)
    candidate = _load_report(args.candidate)
    keys = ("macro_recall", "micro_recall", "ndcg", "mrr")
    dropped = 0
    for key in keys:
        before = float(baseline[key])
        after = float(candidate[key])
        delta = after - before
        failed = delta < -args.tolerance
        dropped += int(failed)
        mark = "DROP" if failed else "ok  "
        print(f"{mark} {key:12s} {before:.4f} -> {after:.4f}  ({delta:+.4f})")
    if dropped:
        message = f"compare: {dropped} metric(s) dropped by more than {args.tolerance}"
        print(message, file=sys.stderr)
        return EXIT_REGRESSION
    print("compare: no metric dropped")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "eval":
            return _run_eval(args)
        if args.command == "search":
            return _run_search(args)
        if args.command == "compare":
            return _run_compare(args)
        from .selftest import run_selftest

        return EXIT_OK if run_selftest() else EXIT_REGRESSION
    except (InputError, ValueError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
