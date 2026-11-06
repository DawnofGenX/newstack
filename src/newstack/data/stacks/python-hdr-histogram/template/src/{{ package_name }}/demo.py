"""Six stories about one claim: a percentile with a bounded error, or no percentile.

Every story ends with ``-> holds`` or ``-> BROKEN``; ``main`` exits 1 when any story
breaks, so the demo is a check as well as an explanation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .histogram import DEFAULT_SIGNIFICANT_BITS, Histogram, relative_error, width_of
from .rng import Rng
from .stats import average_of_percentiles, bytes_per_sample, check, nearest_rank

SAMPLES = 200_000
MEDIAN_US = 12_000.0
SIGMA = 0.6
SEED = 7


@dataclass
class Story:
    title: str
    lines: list[str] = field(default_factory=list)
    held: bool = True

    def say(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def require(self, condition: bool, what: str) -> None:
        self.lines.append(f"  {what}: {'yes' if condition else 'NO'}")
        self.held = self.held and condition

    def line(self) -> str:
        return f"  -> {'holds' if self.held else 'BROKEN'}"


def latencies(
    count: int, *, median: float = MEDIAN_US, sigma: float = SIGMA, seed: int = SEED
) -> list[int]:
    """Positive integer latencies from a lognormal, which is what a real tail looks like."""
    rng = Rng(seed)
    return [max(1, round(rng.lognormal(median, sigma))) for _ in range(count)]


def _story_precision() -> Story:
    story = Story("1. a percentile from a bucket can only be as precise as the bucket")
    values = latencies(SAMPLES)
    histogram = Histogram(DEFAULT_SIGNIFICANT_BITS)
    histogram.record_many(values)
    story.say(f"samples      {len(values)}, significant bits {histogram.significant_bits}")
    story.say(f"buckets      {histogram.buckets_used} used of a layout sized for the value range")
    compared = check(histogram, values)
    story.lines.extend(compared.lines())
    story.require(compared.held(), "every reported percentile within the promise")
    story.require(
        all(row.reported >= row.truth for row in compared.rows),
        "the reported value is never below the truth",
    )
    return story


def _story_exact_counts() -> Story:
    story = Story("2. the count is exact even when the value is not")
    values = latencies(50_000, seed=11)
    histogram = Histogram()
    histogram.record_many(values)
    story.say(f"recorded     {len(values)} sample(s)")
    story.say(f"counted      {histogram.count()} sample(s)")
    total_in_buckets = sum(count for count in histogram.as_dict()["counts"].values())
    story.say(f"in buckets   {total_in_buckets} sample(s)")
    story.require(histogram.count() == len(values), "no sample was dropped")
    story.require(total_in_buckets == len(values), "the buckets add up to the total")
    story.require(histogram.lowest == min(values), "the minimum is exact")
    widest = max(width_of(int(index)) for index in histogram.as_dict()["counts"])
    story.say(f"widest bucket {widest} value(s) — counts exact, values approximate")
    return story


def _story_merge() -> Story:
    story = Story("3. two halves merge into one pass, exactly")
    values = latencies(40_000, seed=13)
    half = len(values) // 2
    left, right = Histogram(), Histogram()
    left.record_many(values[:half])
    right.record_many(values[half:])
    merged = left.merged(right)
    whole = Histogram()
    whole.record_many(values)
    story.say(f"left {left.count()} + right {right.count()} = merged {merged.count()}")
    story.require(merged.count() == whole.count(), "the merged count matches one pass")
    story.require(
        merged.as_dict()["counts"] == whole.as_dict()["counts"],
        "every bucket matches one pass",
    )
    story.require(merged.total_sum == whole.total_sum, "the exact sum matches one pass")
    story.require(
        merged.percentile(99.0) == whole.percentile(99.0),
        "the merged p99 matches one pass",
    )
    return story


def _story_memory() -> Story:
    story = Story("4. memory follows the value range, not the sample count")
    series = latencies(200_000, seed=19)
    small = Histogram()
    small.record_many(series[:1_000])
    large = Histogram()
    large.record_many(series)
    small_bytes, small_buckets = small.bytes_used, small.buckets_used
    large_bytes, large_buckets = large.bytes_used, large.buckets_used
    story.say(f"1,000 samples    {small_bytes} byte(s), {small_buckets} bucket(s) used")
    story.say(f"200,000 samples  {large_bytes} byte(s), {large_buckets} bucket(s) used")
    story.require(large_bytes < 2 * small_bytes, "200x the samples cost less than 2x the bytes")
    story.say(
        f"per sample       1,000: {bytes_per_sample(small, 1_000):.2f} B, "
        f"200,000: {bytes_per_sample(large, 200_000):.4f} B"
    )
    story.require(
        bytes_per_sample(large, 200_000) < bytes_per_sample(small, 1_000) / 10,
        "the per-sample cost falls by more than an order of magnitude",
    )
    story.say("the counters are sized by the values the samples touch; the count only fills them")
    return story


def _story_average_trap() -> Story:
    story = Story("5. the average of two percentiles is not the percentile")
    small = latencies(5_000, median=8_000.0, sigma=0.35, seed=23)
    big = latencies(5_000, median=40_000.0, sigma=0.9, seed=29)
    histograms = []
    for group in (small, big):
        histogram = Histogram()
        histogram.record_many(group)
        histograms.append(histogram)
    joined = histograms[0].merged(histograms[1])
    reported = [float(histogram.percentile(95.0)) for histogram in histograms]
    story.say(f"endpoint A p95 {reported[0]:.0f} us, endpoint B p95 {reported[1]:.0f} us")
    averaged = average_of_percentiles([{"p95": reported[0]}, {"p95": reported[1]}], "p95")
    story.say(f"average of the two p95s {averaged:.0f} us")
    story.say(f"p95 of everything       {joined.percentile(95.0)} us")
    truth = nearest_rank(small + big, 95.0)
    story.say(f"p95 of the raw samples  {truth} us")
    story.require(
        abs(joined.percentile(95.0) - truth) / truth <= joined.error,
        "the pooled p95 matches the raw samples",
    )
    story.require(abs(averaged - truth) / truth > 0.2, "the averaged p95 is far from the truth")
    return story


def _story_resolution() -> Story:
    story = Story("6. resolution is a decision you pay for")
    values = latencies(60_000, seed=31)
    story.say(f"{'bits':>5}  {'promised':>10}  {'worst gap':>10}  {'buckets':>8}  {'bytes':>7}")
    rows = []
    for bits in (6, 8, 10, 12, 14):
        histogram = Histogram(bits)
        histogram.record_many(values)
        compared = check(histogram, values, points=(50.0, 99.0, 99.9))
        rows.append((bits, compared))
        story.say(
            f"{bits:>5}  {relative_error(bits) * 100:>9.4f}%  "
            f"{compared.worst * 100:>9.4f}%  {histogram.buckets_used:>8}  "
            f"{histogram.bytes_used:>7}"
        )
    story.require(
        all(compared.held() for _, compared in rows), "every resolution keeps its promise"
    )
    story.require(
        all(rows[i][1].worst >= rows[i + 1][1].worst for i in range(len(rows) - 1)),
        "more bits never make the gap worse",
    )
    return story


STORIES = (
    _story_precision,
    _story_exact_counts,
    _story_merge,
    _story_memory,
    _story_average_trap,
    _story_resolution,
)


def stories() -> list[Story]:
    return [builder() for builder in STORIES]


def render_stories() -> tuple[list[str], bool]:
    lines: list[str] = []
    held = True
    for story in stories():
        lines.append(story.title)
        lines.extend(story.lines)
        lines.append(story.line())
        lines.append("")
        held = held and story.held
    total = len(STORIES)
    summary = f"stories      {total} of {total} hold" if held else "stories      BROKEN"
    lines.append(summary)
    return lines, held


def main() -> int:
    lines, held = render_stories()
    print("\n".join(lines).rstrip())
    return 0 if held else 1


if __name__ == "__main__":
    raise SystemExit(main())
