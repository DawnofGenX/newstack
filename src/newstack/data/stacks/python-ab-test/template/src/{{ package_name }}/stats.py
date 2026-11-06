"""Proportions, intervals, and the arithmetic a p-value hides."""

from __future__ import annotations

import math
from dataclasses import dataclass

Z_95 = 1.959963984540054
TWO = 2.0


class StatsError(ValueError):
    """A number that cannot describe an experiment."""


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(TWO)))


def normal_quantile(p: float) -> float:
    """The z whose left-tail probability is p, by bisection (no table, no lookup)."""
    if not 0.0 < p < 1.0:
        raise StatsError(f"a quantile needs a probability strictly between 0 and 1, not {p}")
    low, high = -40.0, 40.0
    for _ in range(200):
        middle = (low + high) / TWO
        if normal_cdf(middle) < p:
            low = middle
        else:
            high = middle
    return (low + high) / TWO


def two_sided_p(z: float) -> float:
    """The probability of a statistic at least this far from zero, either way."""
    return math.erfc(abs(z) / math.sqrt(TWO))


@dataclass(frozen=True)
class Arm:
    """One side of a test: how many visitors, and how many of them converted."""

    name: str
    conversions: int
    visitors: int

    def __post_init__(self) -> None:
        if not self.name:
            raise StatsError("an arm needs a name")
        for field, value in (("conversions", self.conversions), ("visitors", self.visitors)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise StatsError(f"arm {self.name!r} has a non-integer {field}: {value!r}")
        if self.visitors < 1:
            raise StatsError(f"arm {self.name!r} has no visitors, so it has no rate")
        if self.conversions < 0:
            raise StatsError(f"arm {self.name!r} counts {self.conversions} conversions")
        if self.conversions > self.visitors:
            raise StatsError(
                f"arm {self.name!r} counts {self.conversions} conversions among "
                f"{self.visitors} visitors, which is impossible"
            )

    @property
    def rate(self) -> float:
        return self.conversions / self.visitors

    @classmethod
    def from_text(cls, text: str) -> Arm:
        """Parse `name=conversions/visitors`, e.g. `control=100/1000`."""
        if "=" not in text:
            raise StatsError(f"{text!r} is not an arm; write name=conversions/visitors")
        name, _, numbers = text.partition("=")
        left, _, right = numbers.partition("/")
        try:
            conversions, visitors = int(left), int(right)
        except ValueError as error:
            raise StatsError(f"{text!r} does not hold two whole numbers") from error
        return cls(name.strip(), conversions, visitors)


def standard_error(left: Arm, right: Arm) -> float:
    """The unpooled error of the difference: what the interval is built on."""
    return math.sqrt(
        left.rate * (1.0 - left.rate) / left.visitors
        + right.rate * (1.0 - right.rate) / right.visitors
    )


def pooled_error(control: Arm, treatment: Arm) -> float:
    """The pooled error: what the test is built on, because H0 says one rate."""
    total = control.visitors + treatment.visitors
    shared = (control.conversions + treatment.conversions) / total
    return math.sqrt(shared * (1.0 - shared) * (1.0 / control.visitors + 1.0 / treatment.visitors))


@dataclass(frozen=True)
class Interval:
    low: float
    high: float

    def contains(self, value: float) -> bool:
        return self.low <= value <= self.high

    def text(self) -> str:
        return f"[{self.low:+.4f}, {self.high:+.4f}]"


def wilson(conversions: int, visitors: int, z: float = Z_95) -> Interval:
    """The interval for ONE rate, which behaves at the edges where Wald does not."""
    if visitors < 1:
        raise StatsError("an interval needs at least one visitor")
    rate = conversions / visitors
    denominator = 1.0 + z * z / visitors
    middle = (rate + z * z / (2.0 * visitors)) / denominator
    spread = z * math.sqrt(rate * (1.0 - rate) / visitors + z * z / (4.0 * visitors**2))
    return Interval(middle - spread / denominator, middle + spread / denominator)


@dataclass(frozen=True)
class Comparison:
    control: Arm
    treatment: Arm
    alpha: float
    difference: float
    lift: float
    z: float
    p_value: float
    interval: Interval

    def significant(self) -> bool:
        return self.p_value < self.alpha

    def direction(self) -> str:
        if not self.significant():
            return "indistinguishable"
        return "higher" if self.difference > 0 else "lower"

    def lift_interval(self) -> Interval:
        """The relative lift's interval, which is the difference divided by the baseline."""
        if self.control.rate == 0.0:
            raise StatsError("a lift over a zero baseline has no finite interval")
        return Interval(
            self.interval.low / self.control.rate,
            self.interval.high / self.control.rate,
        )

    def lines(self) -> list[str]:
        control_interval = wilson(self.control.conversions, self.control.visitors)
        treatment_interval = wilson(self.treatment.conversions, self.treatment.visitors)
        return [
            f"control      {self.control.name:<10} {self.control.conversions:>7} of "
            f"{self.control.visitors:<7} = {self.control.rate:6.2%}  "
            f"wilson {control_interval.text()}",
            f"treatment    {self.treatment.name:<10} {self.treatment.conversions:>7} of "
            f"{self.treatment.visitors:<7} = {self.treatment.rate:6.2%}  "
            f"wilson {treatment_interval.text()}",
            f"difference   {self.difference:+.4f} ({self.lift:+.2%} relative), "
            f"{self.alpha:.0%} interval {self.interval.text()}",
            f"z            {self.z:+.4f}    two-sided p {self.p_value:.4f}",
            f"verdict      {self.direction()}"
            + ("" if self.significant() else f" at alpha {self.alpha}"),
        ]


def compare(control: Arm, treatment: Arm, alpha: float = 0.05) -> Comparison:
    """A fixed-horizon two-proportion test, with the caveat that it is fixed-horizon."""
    if not 0.0 < alpha < 1.0:
        raise StatsError(f"alpha needs to be a probability, not {alpha}")
    difference = treatment.rate - control.rate
    error = pooled_error(control, treatment)
    if error == 0.0:
        z = 0.0
        p_value = 1.0 if difference == 0.0 else 0.0
    else:
        z = difference / error
        p_value = two_sided_p(z)
    half_width = normal_quantile(1.0 - alpha / TWO) * standard_error(control, treatment)
    interval = Interval(difference - half_width, difference + half_width)
    lift = difference / control.rate if control.rate else math.inf
    return Comparison(control, treatment, alpha, difference, lift, z, p_value, interval)


def sample_per_arm(
    baseline: float,
    relative_lift: float,
    *,
    alpha: float = 0.05,
    power: float = 0.8,
) -> int:
    """How many visitors each arm needs to see a lift this size, or more."""
    if not 0.0 < baseline < 1.0:
        raise StatsError(f"a baseline rate is a probability, not {baseline}")
    if relative_lift == 0.0:
        raise StatsError("a lift of zero needs an infinite sample, because nothing is there")
    treatment = baseline * (1.0 + relative_lift)
    if not 0.0 < treatment < 1.0:
        raise StatsError(f"a {relative_lift:+.1%} lift on {baseline:.2%} leaves the range 0..1")
    if not 0.0 < power < 1.0:
        raise StatsError(f"power is a probability, not {power}")
    z_alpha = normal_quantile(1.0 - alpha / TWO)
    z_power = normal_quantile(power)
    average = (baseline + treatment) / TWO
    spread = math.sqrt(2.0 * average * (1.0 - average))
    parts = math.sqrt(baseline * (1.0 - baseline) + treatment * (1.0 - treatment))
    numerator = z_alpha * spread + z_power * parts
    return math.ceil((numerator / (treatment - baseline)) ** 2)


def detectable_lift(
    baseline: float,
    visitors_per_arm: int,
    *,
    alpha: float = 0.05,
    power: float = 0.8,
) -> float:
    """The smallest relative lift this sample could have caught, by bisection."""
    if visitors_per_arm < 1:
        raise StatsError("a sample needs at least one visitor")
    low, high = 0.0001, 5.0
    for _ in range(200):
        middle = (low + high) / TWO
        if sample_per_arm(baseline, middle, alpha=alpha, power=power) > visitors_per_arm:
            low = middle
        else:
            high = middle
    return (low + high) / TWO
