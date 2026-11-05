"""Five stories about what a Bloom filter can and cannot promise."""

from __future__ import annotations

import math

from .bloom import Bloom, CountingBloom, sized_for
from .measure import false_negatives, false_positive_rate


def _items(count: int, prefix: str = "present") -> list[str]:
    return [f"{prefix}-{number}" for number in range(count)]


def story_no_false_negatives() -> list[str]:
    sizing = sized_for(5_000, 0.01)
    bloom = Bloom(sizing.m_bits, sizing.k_hashes)
    items = _items(5_000)
    for item in items:
        bloom.add(item)
    misses = false_negatives(bloom, items)
    return [
        "1. a filter never says no to something it was told",
        f"  {len(items)} items added to {sizing.m_bits} bits with {sizing.k_hashes} hashes",
        f"  fill              {bloom.fill():.4f}",
        f"  items answering no {len(misses)}",
        "  this is the one guarantee: no false negatives, ever",
    ]


def story_rate_is_measurable() -> list[str]:
    lines = [
        "2. the false-positive rate is a number you can check",
        "  the formula promised a rate; 20000 absent items were then probed",
        f"  {'target':>8}  {'bits':>7}  {'k':>2}  {'predicted':>9}  {'measured':>9}",
    ]
    for relative in (70, 100, 125):
        target = 0.01 * relative / 100
        sizing = sized_for(2_000, target)
        bloom = Bloom(sizing.m_bits, sizing.k_hashes)
        for item in _items(2_000):
            bloom.add(item)
        measured = false_positive_rate(bloom)
        lines.append(
            f"  {target:8.4f}  {sizing.m_bits:7d}  {sizing.k_hashes:2d}  "
            f"{sizing.predicted_rate:9.4f}  {measured:9.4f}"
        )
    lines.append("  the bits-per-item budget moves the rate, not the promise")
    return lines


def story_more_hashes_is_not_better() -> list[str]:
    sizing = sized_for(2_000, 0.01)
    lines = [
        "3. past the optimum, more hashes make it worse",
        f"  {sizing.m_bits} bits fixed, 2000 items, sweep the hash count",
        "  k   predicted  measured",
    ]
    best = (1.0, 0)
    for k_hashes in range(1, 13):
        bloom = Bloom(sizing.m_bits, k_hashes)
        for item in _items(2_000):
            bloom.add(item)
        predicted = (1 - math.exp(-k_hashes * 2_000 / sizing.m_bits)) ** k_hashes
        measured = false_positive_rate(bloom, 4_000)
        if measured < best[0]:
            best = (measured, k_hashes)
        marker = " <- best" if k_hashes == sizing.k_hashes else ""
        lines.append(f"  {k_hashes:2d}  {predicted:9.4f}  {measured:8.4f}{marker}")
    lines.append(
        f"  measured minimum at k={best[1]} ({best[0]:.4f}); the textbook choice was "
        f"k={sizing.k_hashes}"
    )
    return lines


def _sharing_pair(bloom: Bloom, candidates: list[str]) -> tuple[str, ...]:
    """Find two items that share a bit, so removal can be shown breaking one."""
    seen: dict[int, str] = {}
    for item in candidates:
        for pos in bloom.positions(item):
            other = seen.get(pos)
            if other is not None and other != item:
                return other, item
            seen[pos] = item
    raise RuntimeError("no sharing pair among the candidates")


def story_removal_breaks_it() -> list[str]:
    sizing = sized_for(10, 0.01)
    naive = Bloom(sizing.m_bits, sizing.k_hashes)
    counting = CountingBloom(sizing.m_bits, sizing.k_hashes)
    candidates = _items(400, "candidate")
    keeper, dropped = _sharing_pair(naive, candidates)
    lines = [
        "4. removal is where the guarantee dies, and counters are the way back",
        f"  {keeper} and {dropped} share at least one position",
    ]
    for bloom in (naive, counting):
        bloom.add(keeper)
        bloom.add(dropped)
    naive.clear(dropped)
    counting.remove(dropped)
    lines += [
        f"  after clearing the bits of {dropped}:",
        f"    plain filter     {keeper} present = {naive.might_contain(keeper)}",
        f"    counting filter  {keeper} present = {counting.might_contain(keeper)}",
        "  clearing erased a bit the keeper needed; decrementing only removed one count",
    ]
    return lines


def story_saturation() -> list[str]:
    sizing = sized_for(1_000, 0.01)
    bloom = Bloom(sizing.m_bits, sizing.k_hashes)
    for item in _items(20_000, "overflow"):
        bloom.add(item)
    measured = false_positive_rate(bloom, 1_000)
    estimate = bloom.estimate_items()
    lines = [
        "5. saturation is the failure mode nobody notices",
        f"  {sizing.m_bits} bits sized for 1000 items, 20000 items added",
        f"  fill              {bloom.fill():.4f}",
        f"  estimated items   {estimate:.0f}" if estimate is not None else "  estimated items   -",
        f"  predicted rate    {bloom.predict_rate():.4f}",
        f"  measured rate     {measured:.4f}",
        "  at fill 1.0 every lookup answers yes, and the fill is the only warning",
    ]
    return lines


STORIES = (
    story_no_false_negatives,
    story_rate_is_measurable,
    story_more_hashes_is_not_better,
    story_removal_breaks_it,
    story_saturation,
)


def render() -> list[str]:
    lines: list[str] = []
    for story in STORIES:
        lines.extend(story())
        lines.append("")
    return lines
