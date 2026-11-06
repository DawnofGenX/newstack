"""The command line: signatures, one comparison, a candidate set, or a clustering."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .dedupe import DedupeError, cluster
from .lsh import Bands, LshError, pick
from .measure import evaluate
from .minhash import MinHash, MinHashError
from .shingles import ShingleError, jaccard, shingles

PROGRAM = "{{ npm_name }}"
VERSION = __version__

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_UNUSABLE = 2

DEFAULT_WIDTH = 128
DEFAULT_SHINGLE = 5
DEFAULT_THRESHOLD = 0.8


class UsageError(ValueError):
    """A request the command line cannot answer."""


def load_corpus(path: Path) -> list[tuple[str, str]]:
    """Read a JSONL corpus: one object per line with a name and a text."""
    if not path.exists():
        raise UsageError(f"{path} does not exist")
    documents: list[tuple[str, str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise UsageError(f"{path}:{number} is not JSON: {error.msg}") from error
        if not isinstance(payload, dict) or "name" not in payload or "text" not in payload:
            raise UsageError(f"{path}:{number} needs a 'name' and a 'text'")
        documents.append((str(payload["name"]), str(payload["text"])))
    if not documents:
        raise UsageError(f"{path} holds no documents")
    return documents


def read_text(path: Path) -> str:
    if not path.exists():
        raise UsageError(f"{path} does not exist")
    return path.read_text(encoding="utf-8")


def _bands(arguments: argparse.Namespace, width: int) -> Bands:
    if arguments.bands and arguments.rows:
        chosen = Bands(arguments.bands, arguments.rows)
        if chosen.width > width:
            raise UsageError(
                f"{chosen.describe()} needs {chosen.width} position(s) "
                f"but the signature holds {width}"
            )
        return chosen
    if arguments.bands or arguments.rows:
        raise UsageError("--bands and --rows belong together")
    return pick(width, arguments.threshold)


def _command_signature(arguments: argparse.Namespace) -> int:
    scheme = MinHash(arguments.width, shingle_size=arguments.shingle)
    text = read_text(arguments.text) if arguments.text else arguments.string
    if not text:
        raise UsageError("a signature needs --text FILE or --string TEXT")
    signature = scheme.signature(text)
    items = shingles(text, arguments.shingle)
    if arguments.json:
        print(
            json.dumps(
                {
                    "width": scheme.width,
                    "shingle_size": scheme.shingle_size,
                    "shingles": len(items),
                    "deviation": scheme.error,
                    "signature": list(signature),
                },
                indent=2,
            )
        )
        return EXIT_OK
    print(f"shingles     {len(items)} of {arguments.shingle} word(s) each")
    print(f"width        {scheme.width} positions, deviation {scheme.error:.4f}")
    print(f"signature    {','.join(str(value) for value in signature)}")
    return EXIT_OK


def _command_similar(arguments: argparse.Namespace) -> int:
    left, right = read_text(arguments.left), read_text(arguments.right)
    left_set, right_set = shingles(left, arguments.shingle), shingles(right, arguments.shingle)
    exact = jaccard(left_set, right_set)
    scheme = MinHash(arguments.width, shingle_size=arguments.shingle)
    estimate = scheme.estimate(scheme.signature(left), scheme.signature(right))
    if arguments.json:
        print(
            json.dumps(
                {
                    "exact": exact,
                    "estimate": estimate,
                    "deviation": scheme.error,
                    "threshold": arguments.threshold,
                    "similar": estimate >= arguments.threshold,
                },
                indent=2,
            )
        )
        return EXIT_OK if estimate >= arguments.threshold else EXIT_REFUSED
    print(f"shingles     {len(left_set)} and {len(right_set)} at {arguments.shingle} word(s)")
    print(f"exact        jaccard {exact:.4f}")
    print(
        f"estimate     {estimate:.4f} from {scheme.width} positions (deviation {scheme.error:.4f})"
    )
    print(
        f"threshold    {arguments.threshold:.2f}: "
        f"{'similar' if estimate >= arguments.threshold else 'different'}"
    )
    return EXIT_OK if estimate >= arguments.threshold else EXIT_REFUSED


def _command_candidates(arguments: argparse.Namespace) -> int:
    documents = load_corpus(arguments.corpus)
    bands = _bands(arguments, arguments.width)
    report = evaluate(
        documents,
        width=arguments.width,
        bands=bands,
        threshold=arguments.threshold,
        shingle_size=arguments.shingle,
    )
    if arguments.json:
        print(
            json.dumps(
                {
                    "documents": report.documents,
                    "all_pairs": report.all_pairs,
                    "candidates": report.candidates,
                    "reduction": report.reduction,
                    "true_pairs": report.true_pairs,
                    "found": report.found,
                    "missed": report.missed,
                    "recall": report.recall,
                    "precision": report.precision,
                },
                indent=2,
            )
        )
        return EXIT_OK
    for line in report.lines():
        print(line)
    return EXIT_OK


def _command_dedupe(arguments: argparse.Namespace) -> int:
    documents = load_corpus(arguments.corpus)
    scheme = MinHash(arguments.width, shingle_size=arguments.shingle)
    signatures = {name: scheme.signature(text) for name, text in documents}
    groups = cluster(signatures, _bands(arguments, arguments.width), threshold=arguments.threshold)
    if arguments.json:
        print(
            json.dumps(
                {
                    "clusters": [list(cluster) for cluster in groups.clusters],
                    "duplicates": groups.duplicates,
                    "joined": groups.joined,
                    "rejected": groups.rejected,
                },
                indent=2,
            )
        )
    else:
        for line in groups.lines():
            print(line)
    if arguments.fail_on_duplicates and groups.duplicates:
        return EXIT_REFUSED
    return EXIT_OK


def _command_curve(arguments: argparse.Namespace) -> int:
    bands = _bands(arguments, arguments.width)
    print(f"banding      {bands.describe()}")
    print(f"half-way     similarity {bands.threshold():.3f}")
    print("similarity   probability")
    for similarity, probability in bands.curve(arguments.points):
        print(f"{similarity:>10.2f}   {probability:>11.4f}")
    return EXIT_OK


def _command_demo(arguments: argparse.Namespace) -> int:
    del arguments
    from . import demo

    return demo.main()


def _command_selftest(arguments: argparse.Namespace) -> int:
    del arguments
    from . import selftest

    return selftest.main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Near-duplicate detection: MinHash signatures, LSH banding, measured recall.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)

    def add_common(target: argparse.ArgumentParser) -> None:
        target.add_argument("--width", type=int, default=DEFAULT_WIDTH)
        target.add_argument("--shingle", type=int, default=DEFAULT_SHINGLE)

    signature = commands.add_parser("signature", help="print a document's signature")
    signature.add_argument("--text", type=Path, help="a file to read")
    signature.add_argument("--string", default="", help="text on the command line")
    signature.add_argument("--json", action="store_true")
    add_common(signature)
    signature.set_defaults(handler=_command_signature)

    similar = commands.add_parser("similar", help="compare two documents")
    similar.add_argument("--left", type=Path, required=True)
    similar.add_argument("--right", type=Path, required=True)
    similar.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    similar.add_argument("--json", action="store_true")
    add_common(similar)
    similar.set_defaults(handler=_command_similar)

    candidates = commands.add_parser("candidates", help="what the banding would compare")
    candidates.add_argument("--corpus", type=Path, required=True)
    candidates.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    candidates.add_argument("--bands", type=int, default=0)
    candidates.add_argument("--rows", type=int, default=0)
    candidates.add_argument("--json", action="store_true")
    add_common(candidates)
    candidates.set_defaults(handler=_command_candidates)

    dedupe = commands.add_parser("dedupe", help="cluster near-duplicates")
    dedupe.add_argument("--corpus", type=Path, required=True)
    dedupe.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    dedupe.add_argument("--bands", type=int, default=0)
    dedupe.add_argument("--rows", type=int, default=0)
    dedupe.add_argument("--fail-on-duplicates", action="store_true")
    dedupe.add_argument("--json", action="store_true")
    add_common(dedupe)
    dedupe.set_defaults(handler=_command_dedupe)

    curve = commands.add_parser("curve", help="the S-curve of a banding")
    curve.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    curve.add_argument("--points", type=int, default=11)
    curve.add_argument("--bands", type=int, default=0)
    curve.add_argument("--rows", type=int, default=0)
    add_common(curve)
    curve.set_defaults(handler=_command_curve)

    demo = commands.add_parser("demo", help="six stories, each of which must hold")
    demo.set_defaults(handler=_command_demo)

    selftest = commands.add_parser("selftest", help="the rules as in-process checks")
    selftest.set_defaults(handler=_command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        return int(arguments.handler(arguments))
    except (UsageError, ShingleError, MinHashError, LshError, DedupeError, ValueError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
