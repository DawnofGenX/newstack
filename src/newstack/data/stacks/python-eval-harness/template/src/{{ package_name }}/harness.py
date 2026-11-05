"""Turning examples plus predictions into a report.

The rule this module exists to enforce: an example whose prediction is missing
scores zero. Dropping it instead would make a model that answered 3 of 100
questions look perfect on the ones it answered — which is exactly the bug that
makes published benchmark numbers unreproducible.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from . import metrics
from .dataset import Example


@dataclass(frozen=True)
class Report:
    metric: str
    scores: dict[str, float]
    missing: tuple[str, ...]
    unused: tuple[str, ...]

    @property
    def total(self) -> int:
        return len(self.scores)

    @property
    def answered(self) -> int:
        return self.total - len(self.missing)

    @property
    def score(self) -> float:
        return sum(self.scores.values()) / self.total if self.scores else 0.0

    def summary(self) -> dict:
        return {
            "metric": self.metric,
            "score": round(self.score, 6),
            "examples": self.total,
            "answered": self.answered,
            "missing": list(self.missing),
            "unused": list(self.unused),
            "scores": dict(sorted(self.scores.items())),
        }


def evaluate(
    examples: Sequence[Example],
    predictions: Mapping[str, str],
    metric: str = metrics.DEFAULT_METRIC,
) -> Report:
    score_one: Callable[[str, str], float] = metrics.get(metric)
    scores = {
        example.id: score_one(predictions.get(example.id, ""), example.gold) for example in examples
    }
    known = {example.id for example in examples}
    missing = tuple(example.id for example in examples if example.id not in predictions)
    unused = tuple(sorted(set(predictions) - known))
    return Report(metric=metric, scores=scores, missing=missing, unused=unused)
