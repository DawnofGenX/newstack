"""Shared fixtures: the shipped corpus, its judgements, and one scored report."""

from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }}.chunk import chunk_corpus
from {{ package_name }}.evaluate import Report, evaluate
from {{ package_name }}.qrels import Qrels, load_corpus, load_qrels

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "fixtures" / "corpus"
QRELS_PATH = ROOT / "fixtures" / "qrels.json"


@pytest.fixture(scope="session")
def corpus() -> dict[str, str]:
    return load_corpus(CORPUS_PATH)


@pytest.fixture(scope="session")
def qrels() -> Qrels:
    return load_qrels(QRELS_PATH)


@pytest.fixture(scope="session")
def report(corpus: dict[str, str], qrels: Qrels) -> Report:
    return evaluate(corpus, qrels.queries, k=qrels.k)


@pytest.fixture(scope="session")
def sparse(corpus: dict[str, str]) -> int:
    """Number of chunks with no overlap at all."""
    return len(chunk_corpus(corpus, size=12, overlap=0))
