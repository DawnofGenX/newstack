"""Loading the two inputs: a directory of documents and a file of judgements."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class InputError(ValueError):
    """The corpus or the judgements cannot be used as given."""


@dataclass(frozen=True)
class Qrels:
    k: int
    queries: dict[str, dict[str, int]]


def load_corpus(directory: Path) -> dict[str, str]:
    """Every `.md` file, keyed by file name, read as UTF-8."""
    if not directory.is_dir():
        raise InputError(f"corpus directory not found: {directory}")
    documents: dict[str, str] = {}
    for path in sorted(directory.glob("*.md")):
        documents[path.name] = path.read_text(encoding="utf-8")
    if not documents:
        raise InputError(f"no .md files in {directory}")
    return documents


def load_qrels(path: Path, fallback_k: int = 3) -> Qrels:
    """The judgement file, with the mistakes that make a report meaningless refused.

    A grade that is not a non-negative integer, a judged document that is not in the
    corpus, and a duplicate query all produce a number that looks plausible and
    measures something else.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InputError(f"judgement file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise InputError(f"{path}: not JSON ({error.msg} at line {error.lineno})") from error

    if not isinstance(raw, dict) or not isinstance(raw.get("queries"), dict):
        raise InputError(f"{path}: expected an object with a 'queries' member")
    if not raw["queries"]:
        raise InputError(f"{path}: no queries to evaluate")

    queries: dict[str, dict[str, int]] = {}
    for query, judgements in raw["queries"].items():
        if not isinstance(judgements, dict):
            raise InputError(f"{query!r}: expected an object of document -> grade")
        grades: dict[str, int] = {}
        for doc_id, grade in judgements.items():
            if not isinstance(grade, int) or isinstance(grade, bool) or grade < 0:
                raise InputError(f"{query!r}: grade for {doc_id!r} must be a non-negative integer")
            grades[doc_id] = grade
        queries[query] = grades

    k = raw.get("k", fallback_k)
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise InputError(f"{path}: 'k' must be a positive integer")
    return Qrels(k=k, queries=queries)


def check_documents_exist(corpus: dict[str, str], qrels: Qrels) -> None:
    """A judged file name with no document behind it can never be retrieved.

    Without this check the query simply scores lower, and the drop looks like a
    retrieval regression rather than a typo in the labels.
    """
    missing = sorted(
        {
            doc_id
            for judgements in qrels.queries.values()
            for doc_id in judgements
            if doc_id not in corpus
        }
    )
    if missing:
        raise InputError(f"judged documents not in the corpus: {', '.join(missing)}")
