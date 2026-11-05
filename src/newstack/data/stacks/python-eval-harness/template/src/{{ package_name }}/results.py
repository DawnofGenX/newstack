"""The artifact a run leaves behind, and the diff between two of them.

A score with no provenance is folklore. Every record carries the commit it was
produced from, the metric, the missing ids, and the per-example scores, so
"the new prompt is better" can be checked example by example instead of trusted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .harness import Report

FORMAT = 1


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build(
    report: Report,
    *,
    run_id: str,
    commit: str | None = None,
    created: str | None = None,
) -> dict:
    return {
        "format": FORMAT,
        "run_id": run_id,
        "created": created or now(),
        "commit": commit,
        **report.summary(),
    }


def write(path: str | Path, record: dict) -> None:
    Path(path).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Comparison:
    baseline: str
    candidate: str
    delta: float
    regressions: tuple[tuple[str, float, float], ...]
    improvements: tuple[tuple[str, float, float], ...]
    only_in_baseline: tuple[str, ...]
    only_in_candidate: tuple[str, ...]
    tolerance: float

    @property
    def regressed(self) -> bool:
        return bool(self.regressions)


def compare(baseline: dict, candidate: dict, *, tolerance: float = 0.0) -> Comparison:
    """Diff two records by aggregate score and then by example.

    ``tolerance`` is the slack a per-example change gets before it counts: with
    ``tolerance=0.01`` a drop of exactly 1e-2 is still a regression, because the
    comparison is strict.
    """

    before = {key: float(value) for key, value in baseline.get("scores", {}).items()}
    after = {key: float(value) for key, value in candidate.get("scores", {}).items()}
    shared = sorted(set(before) & set(after))

    regressions = tuple(
        (key, before[key], after[key]) for key in shared if after[key] < before[key] - tolerance
    )
    improvements = tuple(
        (key, before[key], after[key]) for key in shared if after[key] > before[key] + tolerance
    )
    return Comparison(
        baseline=str(baseline.get("run_id", "baseline")),
        candidate=str(candidate.get("run_id", "candidate")),
        delta=round(float(candidate.get("score", 0.0)) - float(baseline.get("score", 0.0)), 6),
        regressions=regressions,
        improvements=improvements,
        only_in_baseline=tuple(sorted(set(before) - set(after))),
        only_in_candidate=tuple(sorted(set(after) - set(before))),
        tolerance=tolerance,
    )
