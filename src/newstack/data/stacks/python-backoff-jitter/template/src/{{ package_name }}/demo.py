"""Six claims about retry scheduling, each one measured on the same outage."""

from __future__ import annotations

from dataclasses import dataclass

from .policies import Decorrelated, EqualJitter, Exponential, Fixed, FullJitter
from .simulate import Result, decreases, delay_series, simulate

CLIENTS = 200
SEED = 7
FAIL_MS = 1_000.0
BUCKET_MS = 10.0


@dataclass(frozen=True)
class Story:
    title: str
    lines: tuple[str, ...]
    held: bool

    def render(self) -> list[str]:
        verdict = "holds" if self.held else "BROKEN"
        return [self.title, *(f"  {line}" for line in self.lines), f"  -> {verdict}", ""]


def run(policy) -> Result:
    return simulate(policy, clients=CLIENTS, seed=SEED, fail_ms=FAIL_MS, bucket_ms=BUCKET_MS)


def row(label: str, result: Result) -> str:
    return (
        f"{label:<15}{result.peak_retries:>6}{result.buckets_used:>9}"
        f"{result.retries:>9}{result.done_ms:>10.0f}"
    )


def table_head() -> str:
    return f"{'policy':<15}{'peak':>6}{'buckets':>9}{'retries':>9}{'settled':>10}"


def pile_up_story() -> Story:
    fixed = run(Fixed(100.0))
    expo = run(Exponential(100.0, 2.0, 1_000.0))
    lines = [table_head(), row("fixed 100 ms", fixed), row("exponential", expo)]
    lines.append(f"the first wave is unavoidable: {CLIENTS} clients learn of the outage at once")
    lines.append(f"the second wave is a choice: fixed sends {fixed.peak_retries} back together, "
                 f"exponential still sends {expo.peak_retries}")
    return Story(
        "1. a delay without jitter keeps the population synchronised",
        tuple(lines),
        fixed.peak_retries == CLIENTS and expo.peak_retries == CLIENTS,
    )


def spread_story() -> Story:
    fixed = run(Fixed(100.0))
    full = run(FullJitter(100.0, 2.0, 1_000.0))
    equal = run(EqualJitter(100.0, 2.0, 1_000.0))
    lines = [table_head(), row("fixed 100 ms", fixed), row("full jitter", full),
             row("equal jitter", equal)]
    factor = fixed.peak_retries / max(1, full.peak_retries)
    lines.append(f"full jitter cuts the peak {factor:.1f}x while retrying "
                 f"{full.retries} times against {fixed.retries}")
    return Story(
        "2. jitter spreads the same clients over many more buckets",
        tuple(lines),
        full.peak_retries * 3 <= fixed.peak_retries and full.buckets_used > 10 * fixed.buckets_used,
    )


def clock_story() -> Story:
    fixed = run(Fixed(100.0))
    full = run(FullJitter(100.0, 2.0, 1_000.0))
    lines = [
        f"fixed        calm no, settled {fixed.done_ms:>6.0f} ms",
        f"full jitter  calm yes, settled {full.done_ms:>6.0f} ms",
        f"the premium is {full.done_ms - fixed.done_ms:.0f} ms of extra outage for "
        f"{fixed.peak_retries - full.peak_retries} fewer simultaneous retries",
        "a policy that hides this trade is selling one number and hiding the other",
    ]
    return Story(
        "3. the calm is paid for in wall clock time",
        tuple(lines),
        full.done_ms > fixed.done_ms,
    )


def work_story() -> Story:
    expo = run(Exponential(100.0, 2.0, 1_000.0))
    decor = run(Decorrelated(100.0, 1_000.0))
    lines = [table_head(), row("exponential", expo), row("decorrelated", decor)]
    lines.append(f"decorrelated retries {expo.retries - decor.retries} fewer times than "
                 f"exponential and its peak is {decor.peak_retries} against {expo.peak_retries}")
    lines.append("fewer retries is not less strain: the two numbers move independently")
    return Story(
        "4. the number of retries and the size of the wave are different questions",
        tuple(lines),
        decor.retries < expo.retries and decor.peak_retries < expo.peak_retries,
    )


def shape_story() -> Story:
    expo = delay_series(Exponential(100.0, 2.0, 1_000.0), seed=SEED, count=20)
    decor = delay_series(Decorrelated(100.0, 1_000.0), seed=SEED, count=20)
    full = delay_series(FullJitter(100.0, 2.0, 1_000.0), seed=SEED, count=20)
    lines = [
        f"exponential   {', '.join(f'{delay:.0f}' for delay in expo[:6])} ...",
        f"full jitter   {', '.join(f'{delay:.0f}' for delay in full[:6])} ...",
        f"decorrelated  {', '.join(f'{delay:.0f}' for delay in decor[:6])} ...",
        f"waits that got shorter: exponential {decreases(expo)}, "
        f"full jitter {decreases(full)}, decorrelated {decreases(decor)}",
        "decorrelated looks at the previous wait, so its sequence is not a backoff at all",
    ]
    return Story(
        "5. only decorrelated produces a non-monotone sequence",
        tuple(lines),
        decreases(expo) == 0 and decreases(full) > 0 and decreases(decor) > 0,
    )


def seed_story() -> Story:
    first = run(FullJitter(100.0, 2.0, 1_000.0))
    again = run(FullJitter(100.0, 2.0, 1_000.0))
    other = simulate(FullJitter(100.0, 2.0, 1_000.0), clients=CLIENTS, seed=SEED + 1,
                     fail_ms=FAIL_MS, bucket_ms=BUCKET_MS)
    same = (first.peak_retries, first.retries, first.done_ms) == (
        again.peak_retries, again.retries, again.done_ms)
    band = abs(other.peak_retries - first.peak_retries) <= max(5, first.peak_retries)
    lines = [
        f"seed {SEED}      peak {first.peak_retries:>4}, retries {first.retries:>5}, "
        f"settled {first.done_ms:>6.0f} ms",
        f"seed {SEED} again peak {again.peak_retries:>4}, retries {again.retries:>5}, "
        f"settled {again.done_ms:>6.0f} ms",
        f"seed {SEED + 1}     peak {other.peak_retries:>4}, retries {other.retries:>5}, "
        f"settled {other.done_ms:>6.0f} ms",
        "the generator is SplitMix64, so a published curve can be reproduced exactly",
    ]
    return Story(
        "6. the same seed reproduces the same curve",
        tuple(lines),
        same and band,
    )


def stories() -> list[Story]:
    return [
        pile_up_story(),
        spread_story(),
        clock_story(),
        work_story(),
        shape_story(),
        seed_story(),
    ]


def render() -> str:
    lines: list[str] = []
    for story in stories():
        lines.extend(story.render())
    return "\n".join(lines).rstrip() + "\n"
