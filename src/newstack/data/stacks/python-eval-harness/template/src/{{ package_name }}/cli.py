"""The command line: ``run`` an evaluation, or ``compare`` two records."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import dataset, harness, metrics, results
from .dataset import DatasetError


def _commit() -> str | None:
    """Best-effort git commit of the working tree, for the record's provenance."""

    try:
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if head.returncode != 0:
        return None
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5
    )
    suffix = "+dirty" if dirty.stdout.strip() else ""
    return head.stdout.strip() + suffix


def _predictions(path: str):
    """`-` reads the prediction rows from stdin, so a model can pipe them straight in."""

    if path == "-":
        return dataset.parse_predictions(sys.stdin, "<stdin>")
    return dataset.load_predictions(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eh-check",
        description="Score predictions against a gold set, and diff two runs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="score one predictions file")
    run.add_argument("--data", required=True, help="gold JSONL: id, prompt, gold")
    run.add_argument("--predictions", required=True, help='prediction JSONL, or "-" for stdin')
    # No argparse `choices`: an unknown metric has to reach `main` so it can become
    # exit code 2 with a message instead of argparse's own SystemExit.
    names = ", ".join(sorted(metrics.METRICS))
    run.add_argument("--metric", default=metrics.DEFAULT_METRIC, help=f"one of {names}")
    run.add_argument("--out", help="write the full record here (JSON)")
    run.add_argument("--run-id", default=None, help="label for this run; defaults to the file stem")

    cmp_ = sub.add_parser("compare", help="diff two record files")
    cmp_.add_argument("--baseline", required=True)
    cmp_.add_argument("--candidate", required=True)
    cmp_.add_argument("--tolerance", type=float, default=0.0)
    return parser


def _run(args: argparse.Namespace) -> int:
    examples = dataset.load_examples(args.data)
    predictions = _predictions(args.predictions)
    report = harness.evaluate(examples, predictions, args.metric)

    print(f"metric    {report.metric}")
    print(f"score     {report.score:.4f}")
    print(f"answered  {report.answered}/{report.total}")
    if report.missing:
        print(f"missing   {len(report.missing)}: {', '.join(report.missing[:5])}")
    if report.unused:
        print(f"unused    {len(report.unused)}: {', '.join(report.unused[:5])}")

    if args.out:
        default_id = "stdin" if args.predictions == "-" else Path(args.predictions).stem
        run_id = args.run_id or default_id
        record = results.build(report, run_id=str(run_id), commit=_commit())
        results.write(args.out, record)
        print(f"record    {args.out}")
    return 0


def _compare(args: argparse.Namespace) -> int:
    diff = results.compare(
        results.read(args.baseline), results.read(args.candidate), tolerance=args.tolerance
    )
    print(f"baseline  {diff.baseline}")
    print(f"candidate {diff.candidate}")
    print(f"delta     {diff.delta:+.4f}")
    print(f"improved  {len(diff.improvements)}")
    print(f"regressed {len(diff.regressions)}")
    for key, before, after in diff.regressions[:10]:
        print(f"  - {key}: {before:.3f} -> {after:.3f}")
    if diff.only_in_candidate:
        print(f"new ids   {len(diff.only_in_candidate)}")
    if diff.only_in_baseline:
        print(f"gone ids  {len(diff.only_in_baseline)}")
    return 1 if diff.regressed else 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _run(args) if args.command == "run" else _compare(args)
    except (DatasetError, KeyError) as exc:
        print(f"eh-check: {exc}", file=sys.stderr)
        return 2
