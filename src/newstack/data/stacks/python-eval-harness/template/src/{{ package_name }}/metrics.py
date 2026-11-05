"""Scoring functions.

Every metric takes the raw prediction and the raw gold string and returns a
float in [0, 1], so a report can average them without special cases.
"""

from __future__ import annotations

import string
from collections import Counter
from collections.abc import Callable

# Punctuation is dropped before comparing: "Paris." and "paris" are the same
# answer, and a metric that says otherwise measures formatting, not knowledge.
_PUNCTUATION = str.maketrans("", "", string.punctuation)


def normalize(text: str) -> str:
    """Lowercase, strip punctuation, and collapse runs of whitespace."""

    return " ".join(text.lower().translate(_PUNCTUATION).split())


def tokens(text: str) -> list[str]:
    return normalize(text).split()


def exact_match(prediction: str, gold: str) -> float:
    return 1.0 if normalize(prediction) == normalize(gold) else 0.0


def contains(prediction: str, gold: str) -> float:
    """Substring recall: did the prediction mention the gold answer at all?

    Deliberately lenient, and deliberately not the same thing as correct: a model
    that answers "not Paris, it is Lyon" scores 1.0 here.
    """

    gold_tokens = tokens(gold)
    if not gold_tokens:
        return 0.0
    haystack = " ".join(tokens(prediction))
    return 1.0 if " ".join(gold_tokens) in haystack else 0.0


def token_f1(prediction: str, gold: str) -> float:
    """SQuAD-style token F1 over multisets, so repeated words cannot be farmed."""

    predicted = Counter(tokens(prediction))
    expected = Counter(tokens(gold))
    if not predicted or not expected:
        return 0.0
    overlap = sum((predicted & expected).values())
    if overlap == 0:
        return 0.0
    precision = overlap / sum(predicted.values())
    recall = overlap / sum(expected.values())
    return 2 * precision * recall / (precision + recall)


METRICS: dict[str, Callable[[str, str], float]] = {
    "exact_match": exact_match,
    "token_f1": token_f1,
    "contains": contains,
}

DEFAULT_METRIC = "token_f1"


def get(name: str) -> Callable[[str, str], float]:
    try:
        return METRICS[name]
    except KeyError:
        known = ", ".join(sorted(METRICS))
        raise KeyError(f"unknown metric {name!r}; choose one of {known}") from None
