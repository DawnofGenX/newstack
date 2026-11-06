"""Sample-ratio mismatch: the check that runs before anybody reads the lift."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .stats import Arm, StatsError

DEFAULT_ALPHA = 0.001
DEFAULT_SPLIT = 0.5


@dataclass(frozen=True)
class Mismatch:
    ratio: float
    expected: float
    chi_square: float
    p_value: float
    alpha: float

    @property
    def mismatched(self) -> bool:
        return self.p_value < self.alpha

    def lines(self) -> list[str]:
        verdict = "MISMATCH" if self.mismatched else "plausible"
        return [
            f"split        {self.ratio:.4f} against an expected {self.expected:.4f}",
            f"chi-square   {self.chi_square:.3f} on one degree of freedom",
            f"p-value      {self.p_value:.3e}",
            f"verdict      {verdict} at alpha {self.alpha}",
        ]


def chi_square(observed: tuple[int, int], expected: tuple[float, float]) -> float:
    if len(observed) != len(expected):
        raise StatsError("observed and expected need the same number of cells")
    total = sum(observed)
    if total < 1:
        raise StatsError("a mismatch test needs at least one visitor")
    statistic = 0.0
    for seen, share in zip(observed, expected, strict=True):
        if share <= 0.0:
            raise StatsError(f"an expected share must be positive, not {share}")
        predicted = share * total
        statistic += (seen - predicted) ** 2 / predicted
    return statistic


def check(
    control: Arm,
    treatment: Arm,
    *,
    alpha: float = DEFAULT_ALPHA,
    split: float = DEFAULT_SPLIT,
) -> Mismatch:
    """Test that the traffic arrived in the ratio the assignment promised."""
    if not 0.0 < split < 1.0:
        raise StatsError(f"a split is a probability, not {split}")
    total = control.visitors + treatment.visitors
    statistic = chi_square(
        (control.visitors, treatment.visitors), (split, 1.0 - split)
    )
    p_value = math.erfc(math.sqrt(statistic / 2.0))
    return Mismatch(
        ratio=control.visitors / total,
        expected=split,
        chi_square=statistic,
        p_value=p_value,
        alpha=alpha,
    )
