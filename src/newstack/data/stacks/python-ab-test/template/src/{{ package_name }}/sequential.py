"""Peeking, and the boundary that makes it survivable.

A fixed-horizon test is allowed one look. A dashboard is looked at every day,
and every extra look is another chance to cross a line drawn for a single look,
so the real false-positive rate is not the one on the label. The honest answer is
not "do not look": it is a boundary that spends alpha across looks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .rng import Rng, bernoulli
from .stats import Arm, StatsError, compare, normal_cdf, normal_quantile

DEFAULT_LOOKS = 10


def spending(alpha: float, looks: int) -> tuple[float, ...]:
    """How much alpha each look of an O'Brien-Fleming boundary appears to spend.

    The boundary itself is `z_k = z_{alpha/2} / sqrt(t_k)` with `t_k = k / K`: the
    early looks need a huge effect to stop, and the last look needs exactly the
    alpha the fixed-horizon test would have used. Feeding that boundary back
    through the normal gives the per-look alpha shown in the table; the numbers add
    up to MORE than alpha, because the looks are correlated and one world can
    cross at several of them. That is why the demo measures the error rate instead
    of trusting the sum.
    """
    return tuple(2.0 * (1.0 - normal_cdf(critical)) for critical in critical_values(alpha, looks))


def critical_values(alpha: float, looks: int) -> tuple[float, ...]:
    """The O'Brien-Fleming |z| at each look: z_{alpha/2} / sqrt(k / K)."""
    if not 0.0 < alpha < 1.0:
        raise StatsError(f"alpha needs to be a probability, not {alpha}")
    if looks < 1:
        raise StatsError(f"a boundary needs at least one look, not {looks}")
    anchor = normal_quantile(1.0 - alpha / 2.0)
    return tuple(anchor / math.sqrt(look / looks) for look in range(1, looks + 1))


@dataclass(frozen=True)
class Boundary:
    alpha: float
    looks: int
    spent: tuple[float, ...]
    critical: tuple[float, ...]

    def at(self, look: int) -> float:
        if not 1 <= look <= self.looks:
            raise StatsError(f"look {look} is outside 1..{self.looks}")
        return self.critical[look - 1]

    def lines(self) -> list[str]:
        rows = ["look   spent alpha   |z| to cross"]
        for index, (spent, critical) in enumerate(
            zip(self.spent, self.critical, strict=True), start=1
        ):
            rows.append(f"{index:>4}   {spent:>11.5f}   {critical:>11.4f}")
        return rows


def obrien_fleming(alpha: float = 0.05, looks: int = 5) -> Boundary:
    """A boundary whose early looks are strict and whose last look is the plain one."""
    critical = critical_values(alpha, looks)
    return Boundary(alpha=alpha, looks=looks, spent=spending(alpha, looks), critical=critical)


@dataclass(frozen=True)
class Peeking:
    """Three policies, judged on the SAME simulated worlds."""

    baseline: float
    visitors: int
    looks: int
    trials: int
    seed: int
    alpha: float
    fixed_crossings: int
    peeking_crossings: int
    guarded_crossings: int

    def rate(self, crossings: int) -> float:
        return crossings / self.trials

    def lines(self) -> list[str]:
        return [
            f"worlds       {self.trials} trials, both arms truly {self.baseline:.2%}, "
            f"{self.visitors} visitors each",
            f"one look     {self.fixed_crossings:>5} of {self.trials} = "
            f"{self.rate(self.fixed_crossings):6.2%} crossings",
            f"every look   {self.peeking_crossings:>5} of {self.trials} = "
            f"{self.rate(self.peeking_crossings):6.2%} crossings with a flat "
            f"{self.alpha:.0%} line",
            f"boundary     {self.guarded_crossings:>5} of {self.trials} = "
            f"{self.rate(self.guarded_crossings):6.2%} crossings with the spending boundary",
        ]


def simulate(
    *,
    baseline: float = 0.10,
    visitors: int = 2000,
    looks: int = DEFAULT_LOOKS,
    trials: int = 600,
    seed: int = 7,
    alpha: float = 0.05,
) -> Peeking:
    """Run the same worlds through one look, a flat line at every look, and a boundary."""
    if not 0.0 < baseline < 1.0:
        raise StatsError(f"a baseline rate is a probability, not {baseline}")
    if visitors < looks:
        raise StatsError(f"{visitors} visitors cannot fill {looks} looks")
    if trials < 1:
        raise StatsError("a simulation needs at least one trial")
    boundary = obrien_fleming(alpha, looks)
    step = visitors // looks
    fixed = peeking = guarded = 0
    for trial in range(trials):
        control = Rng(seed * 1_000_003 + trial * 2)
        treatment = Rng(seed * 1_000_003 + trial * 2 + 1)
        left = right = 0
        crossed_flat = crossed_guarded = False
        for look in range(1, looks + 1):
            left += bernoulli(control, step, baseline)
            right += bernoulli(treatment, step, baseline)
            result = compare(
                Arm("control", left, look * step),
                Arm("treatment", right, look * step),
                alpha,
            )
            if look == looks:
                fixed += 1 if result.p_value < alpha else 0
            crossed_flat = crossed_flat or abs(result.z) >= boundary.at(looks)
            crossed_guarded = crossed_guarded or abs(result.z) >= boundary.at(look)
        peeking += 1 if crossed_flat else 0
        guarded += 1 if crossed_guarded else 0
    return Peeking(
        baseline=baseline,
        visitors=visitors,
        looks=looks,
        trials=trials,
        seed=seed,
        alpha=alpha,
        fixed_crossings=fixed,
        peeking_crossings=peeking,
        guarded_crossings=guarded,
    )
