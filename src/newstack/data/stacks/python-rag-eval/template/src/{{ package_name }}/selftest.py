"""Check the checker.

Metrics are easy to write and hard to trust: a denominator that shrinks, a ranking
that silently counts chunks instead of documents, or an average that treats a missing
label as a zero all produce a number that looks fine. These checks pin the arithmetic
and the fixture report.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

from .chunk import Chunk, chunk_document, uncovered, words
from .evaluate import evaluate
from .index import BM25
from .metrics import (
    mean,
    ndcg_at_k,
    precision_at_k,
    ranked_documents,
    recall_at_k,
    reciprocal_rank,
)
from .qrels import InputError, check_documents_exist, load_corpus, load_qrels

CORPUS = Path("fixtures/corpus")
QRELS = Path("fixtures/qrels.json")


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []

    def ok(self, label: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            print(f"ok     {label}")
        else:
            self.failed.append(label)
            print(f"FAIL   {label}{': ' + detail if detail else ''}")

    def equal(self, label: str, actual: object, expected: object) -> None:
        self.ok(label, actual == expected, f"expected {expected!r}, got {actual!r}")

    def raises(self, label: str, error: type[Exception], call: Callable[[], object]) -> None:
        try:
            call()
        except error:
            self.ok(label, True)
        except Exception as caught:
            self.ok(label, False, f"raised {type(caught).__name__}: {caught}")
        else:
            self.ok(label, False, "nothing was raised")


TEXT = " ".join(f"w{index}" for index in range(100))


def _chunk_checks(checks: Checks) -> None:
    chunks = chunk_document("doc.md", TEXT, size=40, overlap=10)
    starts = [chunk.start for chunk in chunks]
    ids = [chunk.chunk_id for chunk in chunks]
    checks.equal("100 words become three windows", starts, [0, 30, 60])
    checks.equal("the last window ends at the last word", chunks[-1].end, 100)
    checks.equal("every word is covered", uncovered("doc.md", TEXT, chunks), [])
    checks.equal("ids are offsets, not counters", ids[:2], ["doc.md#0", "doc.md#30"])
    again = chunk_document("doc.md", TEXT, size=40, overlap=10)
    checks.equal("chunking twice gives the same ids", ids, [c.chunk_id for c in again])
    checks.equal("an empty document has no chunks", chunk_document("empty.md", " \n "), [])
    checks.equal("chunks are windows, not sentences", chunks[1].end - chunks[1].start, 40)
    checks.raises(
        "overlap equal to size is refused",
        ValueError,
        lambda: chunk_document("x", TEXT, 20, 20),
    )
    tokens = words("rotate-key.md: yes!")
    checks.equal("punctuation is not a word", tokens, ["rotate", "key", "md", "yes"])


def _metric_checks(checks: Checks) -> None:
    collapsed = ranked_documents(["a#0", "a#30", "b#0"])
    checks.equal("a chunk ranking collapses to documents", collapsed, ["a", "b"])
    checks.equal("recall counts documents", recall_at_k(["a", "b"], {"a", "c"}, 1), 0.5)
    checks.equal("no judgements means no recall", recall_at_k(["a"], set(), 3), None)
    checks.equal("precision divides by k", precision_at_k(["a"], {"a"}, 2), 0.5)
    checks.equal("reciprocal rank of the second slot", reciprocal_rank(["x", "a"], {"a"}), 0.5)
    checks.equal("no relevant document means rr zero", reciprocal_rank(["x"], {"a"}), 0.0)
    perfect = ndcg_at_k(["a", "b"], {"a": 2, "b": 1}, 2)
    checks.equal("a perfect ranking scores 1.0", perfect, 1.0)
    swapped = ndcg_at_k(["b", "a"], {"a": 2, "b": 1}, 2)
    checks.ok("grades make order matter", 0.0 < swapped < 1.0, f"got {swapped}")
    wasted = ndcg_at_k(["x"], {"x": 0}, 1)
    checks.equal("a zero-graded document earns nothing", wasted, 0.0)
    checks.equal("the mean skips missing values", mean([1.0, None, 0.0]), (0.5, 1))


def _index_checks(checks: Checks) -> None:
    chunks = [
        Chunk("a.md", 0, 3, "rotate the signing key"),
        Chunk("b.md", 0, 3, "retry the write"),
    ]
    index = BM25(chunks)
    hits = index.search("signing key", k=2)
    checks.equal("the matching chunk comes first", [hit.doc_id for hit in hits], ["a.md"])
    checks.ok("idf stays positive for a shared term", index.idf("the") > 0, repr(index.idf("the")))
    checks.equal("a query of unknown words returns nothing", index.search("zebra"), [])
    checks.raises("k must be positive", ValueError, lambda: index.search("key", k=0))


def _report_checks(checks: Checks) -> None:
    corpus = load_corpus(CORPUS)
    qrels = load_qrels(QRELS)
    check_documents_exist(corpus, qrels)
    report = evaluate(corpus, qrels.queries, k=qrels.k)
    checks.equal("every query is scored", len(report.scores), len(qrels.queries))
    checks.equal("the unjudged query is skipped, not failed", report.skipped, 1)
    recall = report.macro("recall")
    checks.ok("the fixture corpus is retrievable", recall >= 0.8, str(recall))
    checks.ok("micro recall is a share", 0.0 <= report.micro_recall <= 1.0)

    payload = json.loads(json.dumps(report.as_dict()))
    checks.equal("the report is JSON-serialisable", payload["k"], qrels.k)
    smaller = evaluate(corpus, qrels.queries, size=20, overlap=0)
    checks.ok("a smaller window makes more chunks", smaller.chunks > report.chunks)

    with TemporaryDirectory() as directory:
        broken = Path(directory) / "qrels.json"
        broken.write_text('{"queries": {"q": {"a.md": -1}}}', encoding="utf-8")
        checks.raises("a negative grade is refused", InputError, lambda: load_qrels(broken))
        broken.write_text('{"queries": {"q": {"missing.md": 1}}}', encoding="utf-8")
        checks.raises(
            "a judgement for a missing document is refused",
            InputError,
            lambda: check_documents_exist(corpus, load_qrels(broken)),
        )


def run_selftest() -> bool:
    checks = Checks()
    _chunk_checks(checks)
    _metric_checks(checks)
    _index_checks(checks)
    _report_checks(checks)
    total = checks.passed + len(checks.failed)
    if checks.failed:
        print(f"selftest: {len(checks.failed)} of {total} checks failed")
        return False
    print(f"selftest: {checks.passed} checks passed")
    return True
