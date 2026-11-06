"""Six stories about a layout you can check."""

from __future__ import annotations

from dataclasses import dataclass, field

from .audit import Report, audit, collision
from .generator import ClockError, ManualClock, SnowflakeGenerator
from .layout import (
    EPOCH_MS,
    IDS_PER_MS,
    MAX_SEQUENCE,
    MAX_WORKER,
    WORKERS,
    capacity_lines,
    compose,
    decode,
    years_of_layout,
)


@dataclass
class Story:
    title: str
    lines: list[str] = field(default_factory=list)
    held: bool = True

    def say(self, line: str) -> None:
        self.lines.append(f"  {line}")

    def require(self, condition: bool, claim: str) -> None:
        self.say(f"{claim}: {'yes' if condition else 'NO'}")
        self.held = self.held and condition

    def line(self) -> str:
        return f"  -> {'holds' if self.held else 'BROKEN'}"


def _clock(offset_ms: int = 0) -> ManualClock:
    return ManualClock(EPOCH_MS + offset_ms)


class Frozen:
    """A clock that never moves: the sequence budget really is the end."""

    def __init__(self, now_ms: int) -> None:
        self._now = now_ms

    def now_ms(self) -> int:
        return self._now

    def set(self, now_ms: int) -> None:
        self._now = now_ms

    def wait_until(self, now_ms: int) -> bool:
        return False


def _story_readable() -> Story:
    story = Story("1. an identifier is a timestamp you can read back")
    clock = _clock(1_000)
    worker = SnowflakeGenerator(7, clock=clock)
    first = worker.next_id()
    clock.advance(1)
    second = worker.next_id()
    clock.advance(1)
    third = worker.next_id()
    for value in (first, second, third):
        story.say(decode(value).text())
    fields = [decode(value) for value in (first, second, third)]
    story.require(fields[0].worker == 7, "the worker field survives the round trip")
    story.require(
        [item.sequence for item in fields] == [0, 0, 0], "each millisecond restarts the sequence"
    )
    story.require(
        [item.relative_ms for item in fields] == [1_000, 1_001, 1_002],
        "the time field counts milliseconds",
    )
    return story


def _story_sequence() -> Story:
    story = Story("2. the sequence fills one millisecond, then the clock must move")
    clock = _clock(0)
    worker = SnowflakeGenerator(1, clock=clock)
    values = [worker.next_id() for _ in range(IDS_PER_MS + 904)]
    in_first = sum(1 for value in values if decode(value).relative_ms == 0)
    in_second = len(values) - in_first
    story.say(f"identifiers   {len(values)}")
    story.say(f"in ms 0       {in_first} (the whole sequence is {IDS_PER_MS})")
    story.say(f"in ms 1       {in_second}")
    story.say(f"waits         {worker.waits}")
    story.require(in_first == IDS_PER_MS, "one millisecond holds exactly the sequence")
    story.require(worker.waits == 1, "the overflow waited for the next millisecond")
    story.require(decode(values[-1]).sequence == 903, "the sequence restarts after the wait")
    return story


def _story_rollback() -> Story:
    story = Story("3. a clock that runs backwards: refuse or hold")
    clock = _clock(1_000)
    strict = SnowflakeGenerator(2, clock=clock)
    strict.next_id()
    clock.set(EPOCH_MS + 990)
    try:
        strict.next_id()
    except ClockError as error:
        story.say(f"refuse        {error}")
        refused = True
    else:
        refused = False
    story.require(refused, "the default generator refuses a backwards step")

    clock.set(EPOCH_MS + 1_000)
    holding = SnowflakeGenerator(2, clock=clock, on_rollback="hold")
    holding.next_id()
    clock.set(EPOCH_MS + 990)
    held = [holding.next_id() for _ in range(3)]
    sequences = [decode(value).sequence for value in held]
    story.say(f"hold          sequences {sequences} at ms {decode(held[0]).relative_ms}")
    story.require(sequences == [1, 2, 3], "holding keeps issuing inside the last millisecond")
    story.require(holding.holds == 3, "the holds are counted")

    frozen = Frozen(EPOCH_MS + 1_000)
    spender = SnowflakeGenerator(3, clock=frozen, on_rollback="hold")
    spender.next_id()
    frozen.set(EPOCH_MS + 989)
    spent = 0
    try:
        for _ in range(MAX_SEQUENCE + 5):
            spender.next_id()
            spent += 1
    except ClockError as error:
        story.say(f"exhausted     after {spent}: {error}")
    story.require(spent == MAX_SEQUENCE, "the held sequence is a finite budget")
    return story


def _story_workers() -> Story:
    story = Story("4. two workers in one millisecond cannot collide")
    left, right = collision(0, 1, relative_ms=1_000)
    story.say(f"worker 0      {left}")
    story.say(f"worker 1      {right}")
    story.require(left != right, "the same millisecond and sequence still differ")
    every = {compose(1_000, worker, MAX_SEQUENCE) for worker in range(WORKERS)}
    story.say(f"capacity      {WORKERS} workers x {IDS_PER_MS} = {WORKERS * IDS_PER_MS:,} per ms")
    story.require(len(every) == WORKERS, "every worker has its own number space")
    story.require(
        decode(compose(1_000, MAX_WORKER, MAX_SEQUENCE)).worker == MAX_WORKER,
        "the last worker is still readable",
    )
    return story


def _story_budget() -> Story:
    story = Story("5. the layout is a budget, and it runs out")
    for line in capacity_lines():
        story.say(line)
    story.say(f"per worker    {IDS_PER_MS * 1_000:,} per second")
    story.say(
        f"all workers   {IDS_PER_MS * 1_000 * WORKERS:,} per second, and {WORKERS} is the ceiling"
    )
    story.require(
        years_of_layout() > 69 and years_of_layout() < 70, "41 bits of ms is under seventy years"
    )
    story.require(IDS_PER_MS == 4_096, "12 bits of sequence is 4096 identifiers")
    story.require(WORKERS == 1_024, "10 bits of worker is 1024 workers")
    return story


def _story_order() -> Story:
    story = Story("6. the number order is the field order, not the arrival order")
    clock = _clock(0)
    one = SnowflakeGenerator(0, clock=clock)
    two = SnowflakeGenerator(1, clock=clock)
    values: list[int] = []
    for _ in range(5):
        values.append(one.next_id())
        values.append(two.next_id())
        clock.advance(1)
    ordered = sorted(values)
    story.say(f"arrival        {[decode(value).worker for value in values]}")
    story.say(f"sorted         {[decode(value).worker for value in ordered]}")
    story.require(ordered == values, "the sequence inside one millisecond sorts by worker first")
    report: Report = audit(ordered)
    for line in report.lines():
        story.say(line)
    story.require(report.held(), "no duplicates and no step back")
    story.require(report.workers == (0, 1), "the audit names both workers")
    return story


STORIES = (
    _story_readable,
    _story_sequence,
    _story_rollback,
    _story_workers,
    _story_budget,
    _story_order,
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
    lines.append(f"stories      {total} of {total} hold" if held else "stories      BROKEN")
    return lines, held


def main() -> int:
    lines, held = render_stories()
    print("\n".join(lines).rstrip())
    return 0 if held else 1


if __name__ == "__main__":
    raise SystemExit(main())
