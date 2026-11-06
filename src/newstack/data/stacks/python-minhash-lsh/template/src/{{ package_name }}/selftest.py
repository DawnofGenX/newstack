"""The rules as checks: signatures, banding, candidate sets, and the measurements."""

from __future__ import annotations

import contextlib
import io
import itertools
import json
import tempfile
from pathlib import Path

from . import cli as cli_module
from .corpus import family, pair
from .dedupe import DedupeError, cluster
from .lsh import Bands, LshError, pick
from .measure import estimate_spread, evaluate
from .minhash import MinHash, MinHashError
from .shingles import ShingleError, jaccard, shingles


class Report:
    """A tiny check recorder: every check is one line, failures carry the detail."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool, detail: str = "") -> bool:
        if condition:
            self.passed += 1
            return True
        self.failed += 1
        suffix = f" ({detail})" if detail else ""
        print(f"FAIL {name}{suffix}")
        return False

    def refuses(self, name: str, kind: type[BaseException], action) -> bool:
        try:
            action()
        except kind as error:
            return self.ok(name, True, str(error)[:60])
        except BaseException as error:
            return self.ok(name, False, f"raised {type(error).__name__}")
        return self.ok(name, False, "did not raise")


def _quiet(action) -> int:
    """Run a command with its output captured, returning its exit code."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return action()


def _shingles(report: Report) -> None:
    left = shingles("the quick brown fox jumps over the lazy dog", 3)
    right = shingles("the quick brown fox jumps over the lazy dog", 3)
    report.ok("shingles of the same text are the same set", left == right)
    windowed = shingles("a b c d e f", 5)
    report.ok("a five-word shingle window has the expected count", len(windowed) == 2)
    short = shingles("a b", 5)
    report.ok("a short document is its own single shingle", short == frozenset({"a b"}))
    report.ok(
        "case and punctuation do not change the shingle set",
        shingles("The quick, brown FOX!", 3) == shingles("the quick brown fox", 3),
    )
    report.ok("a document is identical to itself", jaccard(left, left) == 1.0)
    disjoint = jaccard(shingles("a b c", 3), shingles("x y z", 3))
    report.ok("disjoint documents share nothing", disjoint == 0.0)
    report.refuses("shingle size zero is refused", ShingleError, lambda: shingles("a b c", 0))


def _signatures(report: Report) -> None:
    scheme = MinHash(128, shingle_size=5)
    text = "the quick brown fox jumps over the lazy dog and then goes home"
    signature = scheme.signature(text)
    report.ok("a signature has one value per position", len(signature) == 128)
    report.ok("the same text signs the same way", scheme.signature(text) == signature)
    report.ok(
        "the signature of a set and of the text agree",
        scheme.signature_of(shingles(text, 5)) == signature,
    )
    report.ok("a document matches itself exactly", scheme.estimate(signature, signature) == 1.0)
    other = MinHash(64, shingle_size=5)
    elsewhere = other.signature(text)
    report.ok("a different width gives a different signature", len(elsewhere) == 64)
    report.refuses(
        "comparing signatures of different widths is refused",
        MinHashError,
        lambda: scheme.estimate(signature, elsewhere),
    )
    spread = [MinHash(128, seed=seed).signature(text) for seed in (1, 2)]
    report.ok("the seed changes the permutations", spread[0] != spread[1])
    report.ok("the promised deviation is 1/sqrt(width)", abs(MinHash(256).error - 0.0625) < 1e-12)
    report.refuses("width zero is refused", MinHashError, lambda: MinHash(0))


def _banding(report: Report) -> None:
    bands = pick(128, 0.8)
    report.ok("a picked banding uses the whole width", bands.width == 128)
    report.ok(
        "rows times bands is the width",
        bands.bands * bands.rows == 128,
        f"{bands.bands}x{bands.rows}",
    )
    report.ok("the probability at similarity 0 is 0", bands.probability(0.0) == 0.0)
    report.ok("the probability at similarity 1 is 1", abs(bands.probability(1.0) - 1.0) < 1e-12)
    rising = bands.curve(11)
    report.ok(
        "the S-curve rises with similarity",
        all(low[1] <= high[1] + 1e-12 for low, high in itertools.pairwise(rising)),
    )
    report.ok("the threshold lies between 0 and 1", 0.0 < bands.threshold() < 1.0)
    report.ok(
        "the probability at the threshold is about a half",
        abs(bands.probability(bands.threshold()) - 0.5) < 0.15,
        f"{bands.probability(bands.threshold()):.3f}",
    )
    report.refuses("a banding with no bands is refused", LshError, lambda: Bands(0, 16))
    report.refuses(
        "a signature shorter than the banding is refused",
        LshError,
        lambda: Bands(8, 16).buckets(tuple(range(16))),
    )
    scheme = MinHash(128, shingle_size=5)
    one = scheme.signature("the quick brown fox jumps over the lazy dog")
    split = list(one)
    split[0] = (split[0] + 1) % (1 << 61)
    report.ok(
        "one changed band drops the candidate pair",
        Bands(8, 16).candidates({"a": one, "b": tuple(split), "c": one}) != [],
    )
    report.ok(
        "an identical pair is a candidate",
        ("a", "c") in Bands(8, 16).candidates({"a": one, "b": tuple(split), "c": one}),
    )


def _dedupe(report: Report) -> None:
    scheme = MinHash(128, shingle_size=5)
    names = ["same-a", "same-b", "other"]
    texts = {
        "same-a": "the quick brown fox jumps over the lazy dog and then goes home again",
        "same-b": "the quick brown fox jumps over the lazy dog and then goes home again",
        "other": "a completely different sentence about weather and seasons",
    }
    signatures = {name: scheme.signature(texts[name]) for name in names}
    groups = cluster(signatures, Bands(32, 4), threshold=0.5)
    report.ok(
        "the identical pair is clustered",
        any("same-a" in group and "same-b" in group for group in groups.clusters),
    )
    report.ok(
        "the unrelated document stands alone",
        not any("other" in group and len(group) > 1 for group in groups.clusters),
    )
    report.ok(
        "every document appears once",
        sorted(name for group in groups.clusters for name in group) == sorted(names),
    )
    report.ok("the duplicate count is one", groups.duplicates == 1, str(groups.duplicates))
    report.refuses("an empty clustering is refused", DedupeError, lambda: cluster({}, Bands(8, 16)))


def _measurements(report: Report) -> None:
    documents = family(count=60, duplicates=30, replace_every=40)
    bands = Bands(8, 16)
    result = evaluate(documents, width=128, bands=bands, threshold=0.8)
    truth = result.true_pairs
    report.ok("the truth counts both directions of a pair", truth >= 30, str(truth))
    report.ok("the candidate set is smaller than every pair", result.candidates < result.all_pairs)
    report.ok("recall is a fraction", 0.0 <= result.recall <= 1.0)
    report.ok("precision is a fraction", 0.0 <= result.precision <= 1.0)
    report.ok("every candidate pair is verified", result.verified == result.candidates)
    loose = evaluate(documents, width=128, bands=Bands(4, 32), threshold=0.8)
    report.ok(
        "a banding with fewer bands finds fewer pairs",
        loose.candidates <= result.candidates,
        f"{loose.candidates} vs {result.candidates}",
    )
    base, edited, name = pair(replace_every=20)
    rmse, promised, pairs = estimate_spread([(name, base), (f"{name}-edited", edited)], width=512)
    report.ok("the spread measurement covers the pair it was given", pairs >= 1)
    detail = f"{rmse:.4f} vs {promised:.4f}"
    report.ok("the rmse is inside twice the promise", rmse <= 2 * promised, detail)


def _command_line(report: Report) -> None:
    work = Path(tempfile.mkdtemp(prefix="lsh-"))
    corpus = work / "corpus.jsonl"
    base = "the quick brown fox jumps over the lazy dog and then goes home again tonight"
    rows = [
        {"name": "a", "text": base},
        {"name": "b", "text": base},
        {"name": "c", "text": "a different sentence about weather, seasons and the sea"},
    ]
    corpus.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    left, right = work / "left.txt", work / "right.txt"
    left.write_text(base, encoding="utf-8")
    right.write_text(base, encoding="utf-8")

    parsed = cli_module.build_parser().parse_args(["signature", "--string", "x"])
    report.ok(
        "the parser routes a signature without running it",
        parsed.handler is cli_module._command_signature,
    )
    report.ok(
        "a signature prints a width",
        _quiet(lambda: cli_module.main(["signature", "--string", "a b c d e f"])) == 0,
    )
    report.ok(
        "identical files read as similar",
        _quiet(
            lambda: cli_module.main(
                [
                    "similar",
                    "--left",
                    str(left),
                    "--right",
                    str(right),
                ]
            )
        )
        == 0,
    )
    report.ok(
        "unlike files exit 1",
        _quiet(
            lambda: cli_module.main(
                [
                    "similar",
                    "--left",
                    str(left),
                    "--right",
                    str(corpus),
                ]
            )
        )
        == 1,
    )
    report.ok(
        "candidates reads a corpus",
        _quiet(
            lambda: cli_module.main(
                [
                    "candidates",
                    "--corpus",
                    str(corpus),
                ]
            )
        )
        == 0,
    )
    report.ok(
        "dedupe with --fail-on-duplicates exits 1",
        _quiet(
            lambda: cli_module.main(
                [
                    "dedupe",
                    "--corpus",
                    str(corpus),
                    "--fail-on-duplicates",
                    "--threshold",
                    "0.5",
                ]
            )
        )
        == 1,
    )
    report.ok(
        "dedupe alone exits 0",
        _quiet(
            lambda: cli_module.main(
                [
                    "dedupe",
                    "--corpus",
                    str(corpus),
                    "--threshold",
                    "0.5",
                ]
            )
        )
        == 0,
    )
    report.ok("a curve prints", _quiet(lambda: cli_module.main(["curve", "--points", "5"])) == 0)
    report.ok(
        "a missing corpus is exit 2",
        _quiet(
            lambda: cli_module.main(
                [
                    "candidates",
                    "--corpus",
                    str(work / "absent.jsonl"),
                ]
            )
        )
        == 2,
    )
    report.ok(
        "a malformed banding is exit 2",
        _quiet(
            lambda: cli_module.main(
                [
                    "candidates",
                    "--corpus",
                    str(corpus),
                    "--bands",
                    "8",
                ]
            )
        )
        == 2,
    )


def main() -> int:
    report = Report()
    _shingles(report)
    _signatures(report)
    _banding(report)
    _dedupe(report)
    _measurements(report)
    _command_line(report)
    total = report.passed + report.failed
    if report.failed:
        print(f"selftest: {report.failed} of {total} checks failed")
        return 1
    print(f"selftest: {report.passed} checks passed")
    return 0
