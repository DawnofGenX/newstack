"""Six stories about an A/B test, each of which must hold or say it does not."""

from __future__ import annotations

from dataclasses import dataclass

from .sequential import obrien_fleming, simulate
from .srm import check
from .stats import Arm, compare, detectable_lift, sample_per_arm

BASE = 0.10
READERS = 1000


@dataclass(frozen=True)
class Story:
    title: str
    lines: list[str]
    held: bool


def _significant_story() -> Story:
    result = compare(Arm("control", 100, 1000), Arm("treatment", 130, 1000))
    return Story(
        "1. a fixed-horizon test answers one question",
        [
            *result.lines(),
            "the horizon was fixed before the first visitor, so this p-value is the one "
            "on the label",
            "checking after every look would have made it a different, larger number",
        ],
        result.significant() and result.direction() == "higher",
    )


def _peeking_story() -> Story:
    world = simulate(trials=1000, visitors=2000, looks=10, baseline=BASE)
    inflation = world.rate(world.peeking_crossings) / world.rate(world.fixed_crossings)
    return Story(
        "2. every look is another chance to cross the line",
        [
            *world.lines(),
            f"inflation    {inflation:.1f}x the false-positive rate on the same worlds",
            "nothing about the traffic changed; only the number of decisions did",
        ],
        world.peeking_crossings > world.fixed_crossings,
    )


def _boundary_story() -> Story:
    world = simulate(trials=1000, visitors=2000, looks=10, baseline=BASE)
    other = simulate(trials=1000, visitors=2000, looks=10, baseline=0.20, seed=11)
    boundary = obrien_fleming(0.05, world.looks)
    guarded = world.rate(world.guarded_crossings)
    flat = world.rate(world.peeking_crossings)
    return Story(
        "3. a spending boundary buys most of the peeking back",
        [
            f"flat line    {flat:6.2%} of worlds cross a 5% line at some look",
            f"boundary     {guarded:6.2%} of the same worlds cross the boundary",
            f"second world {other.rate(other.guarded_crossings):6.2%} at a 20% baseline, against "
            f"{other.rate(other.peeking_crossings):6.2%} for the flat line",
            f"first look   |z| must reach {boundary.at(1):.2f}, not {boundary.at(world.looks):.2f}",
            f"left over    {guarded - world.alpha:+.2%} against the label: the thresholds treat "
            "the looks as independent, and this simulation is the honest correction",
            "the cost is time, not truth: an effect is declared later, and never falsely sooner",
        ],
        guarded < flat / 2.0,
    )


def _srm_story() -> Story:
    bad = check(Arm("control", 5000, 102_000), Arm("treatment", 5000, 100_000))
    good = check(Arm("control", 5000, 100_200), Arm("treatment", 5000, 100_000))
    return Story(
        "4. a traffic imbalance voids the lift",
        [
            f"one percent   split {bad.ratio:.4f}, p {bad.p_value:.2e}: "
            f"{'MISMATCH' if bad.mismatched else 'plausible'}",
            f"one fifth pct  split {good.ratio:.4f}, p {good.p_value:.3f}: "
            f"{'MISMATCH' if good.mismatched else 'plausible'}",
            "the lift uses the same rows, so a broken split is read as a broken product",
            "run this check first: it is cheap, and it fails before anybody forms an opinion",
        ],
        bad.mismatched and not good.mismatched,
    )


def _power_story() -> Story:
    needed = sample_per_arm(BASE, 0.05)
    small = detectable_lift(BASE, 20_000)
    return Story(
        "5. the sample size is a decision, not a guess",
        [
            "question     a 10.00% baseline, a 5% relative lift, 80% power, alpha 0.05",
            f"needed       {needed:,} visitors per arm",
            f"at 20,000    only a {small:.1%} relative lift would be caught",
            f"at 5,000     only a {detectable_lift(BASE, 5_000):.1%} lift would be caught",
            "an underpowered test does not return 'no'; it returns 'we could not see'",
        ],
        needed > 20_000 and small > 0.05,
    )


def _interval_story() -> Story:
    result = compare(Arm("control", 10, 100), Arm("treatment", 13, 100))
    return Story(
        "6. not significant is not no effect",
        [
            *result.lines(),
            f"the interval runs from {result.interval.low:+.2%} to {result.interval.high:+.2%}",
            "a three-point lift on a hundred visitors is inside the noise of both directions",
            "the sample needed to see it is the number story 5 prints",
        ],
        not result.significant() and result.interval.contains(0.0),
    )


def stories() -> list[Story]:
    return [
        _significant_story(),
        _peeking_story(),
        _boundary_story(),
        _srm_story(),
        _power_story(),
        _interval_story(),
    ]


def render_stories() -> str:
    blocks = []
    for story in stories():
        body = "\n".join(f"  {line}" for line in story.lines)
        verdict = "holds" if story.held else "BROKEN"
        blocks.append(f"{story.title}\n{body}\n  -> {verdict}")
    return "\n\n".join(blocks)


def main() -> int:
    print(render_stories())
    return 0 if all(story.held for story in stories()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
