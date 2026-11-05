"""Six stories about one minute of events, each one a rule the engine keeps."""

from __future__ import annotations

from datetime import UTC, datetime

from .engine import Aggregation, Engine, Report
from .events import US, Event
from .windows import Window

# A whole day boundary, so every timestamp in this demo is a decimal we can read.
BASE_US = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp() * US)


def at(minutes: float = 0.0, seconds: float = 0.0) -> int:
    return BASE_US + int((minutes * 60 + seconds) * US)


def scenario_alignment() -> list[str]:
    engine = Engine(60 * US)
    engine.push(Event(at(seconds=7), 5.0))
    report = engine.report()
    engine.flush()
    report = engine.report()
    window = report.windows[0].window
    return [
        f"event    {Event(at(seconds=7)).at}",
        f"window   {window.label()}",
        f"starts   {window.start} (the epoch's minute, not the first event's)",
    ]


def scenario_late_but_allowed() -> list[str]:
    engine = Engine(60 * US, lateness_us=30 * US, aggregation=Aggregation.COUNT)
    engine.push(Event(at(seconds=10), 1.0))
    engine.push(Event(at(seconds=50), 1.0))
    # The watermark only reaches 10:00:50, so the 10:00 window is still open.
    engine.push(Event(at(minutes=1, seconds=20), 1.0))
    engine.push(Event(at(seconds=40), 1.0))  # 10s late, inside the 30s allowance
    report = engine.report()
    engine.flush()
    report = engine.report()
    window = next(item for item in report.windows if item.window.start_us == at())
    return [
        f"window   {window.window.label()}",
        f"count    {window.count} (the 10:00:40 arrival was 10s late and still counted)",
        f"late     {len(report.late)} event(s) rejected",
        f"final    {window.final}",
    ]


def scenario_too_late() -> list[str]:
    engine = Engine(60 * US, lateness_us=30 * US)
    for moment in (at(seconds=10), at(seconds=50), at(minutes=1, seconds=20)):
        engine.push(Event(moment, 1.0))
    engine.push(Event(at(minutes=3, seconds=30), 1.0))
    before = next(item for item in engine.report().windows if item.window.start_us == at())
    engine.push(Event(at(seconds=30), 1.0))  # long after the window was emitted
    after = next(item for item in engine.report().windows if item.window.start_us == at())
    late = engine.report().late[-1]
    return [
        f"emitted  {before.count} event(s) in {before.window.label()}",
        f"arrived  {late.event.at}, {late.window.label()}",
        f"reason   {late.reason}",
        f"count    {after.count} (unchanged: a late event never rewrites an answer)",
    ]


def scenario_missing() -> list[str]:
    engine = Engine(60 * US)
    for moment in (at(seconds=5), at(minutes=2, seconds=5)):
        engine.push(Event(moment, 1.0))
    engine.flush()
    report = engine.report()
    return [
        f"emitted  {len(report.windows)} window(s) with events",
        f"missing  {', '.join(window.label() for window in report.missing())}",
        "a window with no events has no count; emitting 0 would be a measurement "
        "nobody took",
    ]


def scenario_mean_of_nulls() -> list[str]:
    engine = Engine(60 * US, aggregation=Aggregation.MEAN)
    engine.push(Event(at(seconds=5), None))
    engine.push(Event(at(seconds=6), None))
    engine.flush()
    window = engine.report().windows[0]
    return [
        f"count    {window.count} event(s), {window.with_value} with a value",
        f"mean     {window.value(Aggregation.MEAN)} (- means undefined, not 0)",
        f"total    {window.value(Aggregation.SUM)}",
    ]


def scenario_sliding() -> list[str]:
    engine = Engine(60 * US, hop_us=30 * US)
    engine.push(Event(at(seconds=40), 1.0))
    engine.push(Event(at(minutes=2, seconds=40), 1.0))
    engine.flush()
    report = engine.report()
    lines = [f"event    {Event(at(seconds=40)).at} belongs to both:"]
    for aggregate in report.windows:
        if aggregate.window.start_us <= at(seconds=40) < aggregate.window.end_us:
            lines.append(f"         {aggregate.window.label()}")
    lines.append(f"total    {sum(item.count for item in report.windows[:2])} counts of one event")
    return lines


SCENARIOS = (
    ("alignment belongs to the epoch, not the first event", scenario_alignment),
    ("late within the watermark still counts", scenario_late_but_allowed),
    ("past the watermark the number stands", scenario_too_late),
    ("a window with no events is missing, not zero", scenario_missing),
    ("the mean of nulls is undefined", scenario_mean_of_nulls),
    ("sliding windows count one event in each window", scenario_sliding),
)


def demo() -> list[tuple[str, list[str]]]:
    return [(title, story()) for title, story in SCENARIOS]


def render(report: Report) -> str:
    """A fixed-width table: one line per window, then the late arrivals."""
    width = max([len("window"), *(len(item.window.label()) for item in report.windows)])
    lines = [
        f"aggregation {report.aggregation}  width {report.width_us // US}s"
        f"  hop {'-' if report.hop_us is None else str(report.hop_us // US) + 's'}"
        f"  lateness {report.lateness_us // US}s",
        f"watermark   {'-' if report.watermark_us is None else _iso(report.watermark_us)}",
        "",
        f"{'window':<{width}}{'count':>7}{'total':>12}{'mean':>14}  final",
    ]
    for aggregate in report.windows:
        lines.append(
            f"{aggregate.window.label():<{width}}{aggregate.count:>7}"
            f"{aggregate.value(Aggregation.SUM):>12}{aggregate.value(Aggregation.MEAN):>14}"
            f"  {'yes' if aggregate.final else 'no'}"
        )
    if report.late:
        lines.append("")
        lines.append(f"{len(report.late)} late arrival(s):")
        for late in report.late:
            lines.append(f"  {late.event.at}  {late.window.label()}  {late.reason}")
    missing = report.missing()
    if missing:
        lines.append("")
        lines.append(f"missing ({len(missing)}): {', '.join(w.label() for w in missing)}")
    return "\n".join(lines)


def _iso(t_us: int) -> str:
    from .events import to_iso

    return to_iso(t_us)


def window_of(start_us: int, width_us: int) -> Window:
    return Window(start_us, start_us + width_us)
