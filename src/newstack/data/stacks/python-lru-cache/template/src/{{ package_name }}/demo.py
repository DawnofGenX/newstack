"""Six stories about a cache, each measured on a trace whose shape is printed."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import simulate
from . import trace as trace_module

LENGTH = 20_000
CAPACITY = 100


@dataclass
class Story:
    title: str
    lines: list[str] = field(default_factory=list)
    held: bool = True

    def line(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def require(self, condition: bool) -> None:
        self.held = self.held and condition


def _table(story: Story, results: list[simulate.Metrics]) -> None:
    story.line(simulate.header())
    for result in results:
        story.line(result.line())


def story_popularity() -> Story:
    data = trace_module.zipf_trace(LENGTH)
    ceiling = simulate.ceiling(data, CAPACITY)
    results = simulate.compare(data, CAPACITY)
    story = Story("1. a popularity trace rewards remembering what was used")
    story.line(f"trace        {trace_module.describe('zipf')}")
    story.line(
        f"ceiling      {ceiling:.4f}, the share of accesses to the {CAPACITY} most used keys"
    )
    _table(story, results)
    best = max(result.hit_rate for result in results)
    story.require(best <= ceiling)
    story.require(all(result.hit_rate < ceiling for result in results))
    by_name = {result.policy: result.hit_rate for result in results}
    story.require(by_name["lru"] > by_name["fifo"])
    story.require(by_name["slru"] > by_name["lru"])
    story.line("every policy stays under the ceiling; the ordering between them is the policy")
    return story


def story_loop() -> Story:
    data = trace_module.loop_trace(LENGTH)
    small = simulate.compare(data, 150)
    large = simulate.compare(data, 200)
    story = Story("2. a loop that does not fit is zero for every policy")
    story.line(f"trace        {trace_module.describe('loop')}")
    story.line("capacity 150 of 200 keys")
    _table(story, small)
    story.line("capacity 200 of 200 keys")
    _table(story, large)
    story.require(all(result.hit_rate == 0.0 for result in small))
    story.require(all(result.hit_rate > 0.98 for result in large))
    story.line("no policy can remember a key it had to evict before it came round again")
    return story


def story_scan() -> Story:
    data = trace_module.scan_trace(LENGTH)
    ceiling = simulate.ceiling(data, CAPACITY)
    results = simulate.compare(data, CAPACITY)
    story = Story("3. a sequential scan erases an LRU while a segmented cache survives it")
    story.line(f"trace        {trace_module.describe('scan')}")
    story.line(f"ceiling      {ceiling:.4f}")
    _table(story, results)
    by_name = {result.policy: result.hit_rate for result in results}
    ratio = by_name["slru"] / by_name["lru"]
    story.line(
        f"the segmented cache is {ratio:.2f}x the LRU hit ratio, "
        "because a scan only ever fills its probation area"
    )
    story.require(ratio > 1.2)
    story.require(by_name["slru"] <= ceiling)
    return story


def story_clock() -> Story:
    data = trace_module.zipf_trace(LENGTH)
    results = {result.policy: result for result in simulate.compare(data, CAPACITY)}
    clock, lru = results["clock"], results["lru"]
    story = Story("4. CLOCK buys most of LRU for a sweep instead of a reorder")
    story.line(f"trace        {trace_module.describe('zipf')}")
    story.line(f"lru          {lru.hit_rate:.4f} with {lru.evictions} eviction(s)")
    story.line(
        f"clock        {clock.hit_rate:.4f} with {clock.evictions} eviction(s) "
        f"and {clock.scan_work} slot scan(s)"
    )
    story.line(
        f"difference   {lru.hit_rate - clock.hit_rate:+.4f} of hit rate for "
        f"{clock.scan_work} scan(s) instead of a list move"
    )
    story.require(abs(lru.hit_rate - clock.hit_rate) < 0.02)
    story.require(clock.scan_work > 0)
    return story


def story_capacity() -> Story:
    data = trace_module.zipf_trace(LENGTH)
    capacities = [10, 25, 50, 100, 200, 400]
    story = Story("5. capacity decides more than policy does")
    story.line(f"trace        {trace_module.describe('zipf')}")
    story.line("capacity   lru hit rate   ceiling")
    previous = -1.0
    rising = True
    under = True
    for capacity in capacities:
        rate = simulate.run("lru", data, capacity).hit_rate
        ceiling = simulate.ceiling(data, capacity)
        story.line(f"{capacity:>8}   {rate:>12.4f}   {ceiling:>7.4f}")
        rising = rising and rate > previous
        under = under and rate <= ceiling
        previous = rate
    story.require(rising)
    story.require(under)
    story.line("doubling the capacity moved the LRU twice as far as changing the policy would")
    return story


def story_ranking() -> Story:
    data = trace_module.mixed_trace(LENGTH)
    results = simulate.compare(data, CAPACITY)
    by_name = {result.policy: result.hit_rate for result in results}
    story = Story("6. the trace decides the ranking")
    story.line(f"trace        {trace_module.describe('mixed')}")
    _table(story, results)
    story.line(
        f"on this trace slru is {by_name['slru'] - by_name['lru']:+.4f} against lru, "
        "the opposite of the scan trace"
    )
    story.require(by_name["slru"] < by_name["lru"])
    story.require(by_name["lru"] > by_name["fifo"])
    return story


STORIES = (story_popularity, story_loop, story_scan, story_clock, story_capacity, story_ranking)


def render_stories() -> tuple[list[str], bool]:
    """Every story as text, and whether all of them held."""
    rows: list[str] = []
    held = True
    for builder in STORIES:
        story = builder()
        rows.append(story.title)
        rows.extend(story.lines)
        rows.append(f"  -> {'holds' if story.held else 'BROKEN'}")
        rows.append("")
        held = held and story.held
    return rows, held


def main() -> int:
    rows, held = render_stories()
    print("\n".join(rows))
    return 0 if held else 1
