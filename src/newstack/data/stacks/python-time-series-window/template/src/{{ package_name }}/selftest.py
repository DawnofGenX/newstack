"""Offline checks: every rule the README claims, executed."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .cli import EXIT_LATE, EXIT_OK, EXIT_UNUSABLE, main, parse_duration
from .demo import BASE_US, at, demo
from .engine import Aggregation, Engine, EngineError
from .events import US, Event, EventError, load, to_iso, to_us
from .windows import Window, WindowError, align, containing, covering


class Checker:
    def __init__(self) -> None:
        self.checks = 0
        self.failures = 0

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        self.checks += 1
        if condition:
            return
        self.failures += 1
        print(f"FAIL {name}{': ' + detail if detail else ''}")

    def refuses(self, name: str, fn, kind: type[BaseException]) -> None:
        try:
            fn()
        except kind:
            self.check(name, True)
        except BaseException as error:  
            self.check(name, False, f"raised {type(error).__name__}, wanted {kind.__name__}")
        else:
            self.check(name, False, "it did not raise")


def selftest() -> int:
    c = Checker()

    # -- timestamps ------------------------------------------------------
    c.check("an ISO timestamp with an offset parses", to_us("2026-01-01T00:00:00+00:00") == BASE_US)
    c.check("an integer is already microseconds", to_us("1767225600000000") == BASE_US)
    c.check("to_iso round-trips", to_us(to_iso(BASE_US)) == BASE_US)
    c.refuses("a naive timestamp is refused", lambda: to_us("2026-01-01T00:00:00"), EventError)
    c.refuses("garbage is refused", lambda: to_us("yesterday"), EventError)
    c.refuses("a boolean timestamp is refused", lambda: Event(t_us=True), EventError)
    c.refuses("a boolean value is refused", lambda: Event(t_us=0, value=True), EventError)

    # -- windows ---------------------------------------------------------
    c.check("alignment is to the epoch", align(BASE_US + 7 * US, 60 * US) == BASE_US)
    window = containing(BASE_US + 7 * US, 60 * US)[0]
    c.check(
        "a tiling window is half-open",
        (BASE_US + 59 * US) in window and (BASE_US + 60 * US) not in window,
    )
    c.check(
        "sliding windows all contain the instant",
        all(
            (BASE_US + 40 * US) in item
            for item in containing(BASE_US + 40 * US, 60 * US, 30 * US)
        ),
    )
    c.check("an instant at the hop boundary is in two windows",
          len(containing(BASE_US + 60 * US, 60 * US, 30 * US)) == 2)
    c.refuses("a hop wider than the window is refused",
              lambda: containing(BASE_US, 60 * US, 120 * US), WindowError)
    c.refuses("an empty window is refused", lambda: Window(BASE_US, BASE_US), WindowError)
    c.check("covering spans the range", len(covering(BASE_US, BASE_US + 2 * 60 * US, 60 * US)) == 3)

    # -- aggregation -----------------------------------------------------
    def build(values, *, width=None, hop=None, lateness=0, agg=Aggregation.COUNT):
        engine = Engine(width or 60 * US, hop_us=hop, lateness_us=lateness, aggregation=agg)
        for moment, value in values:
            engine.push(Event(moment, value))
        engine.flush()
        return engine.report()

    report = build([(at(seconds=1), 2.0), (at(seconds=2), 3.0)])
    c.check("count counts events", report.windows[0].count == 2)
    c.check("sum adds the values", report.windows[0].total == 5)
    smallest = report.windows[0].minimum
    largest = report.windows[0].maximum
    c.check("min and max are present", (smallest, largest) == (2, 3))
    mean = build([(at(seconds=1), 2.0), (at(seconds=2), 3.0)], agg=Aggregation.MEAN)
    c.check("mean is the sum over the count", mean.windows[0].mean == 2.5)
    nulls = build([(at(seconds=1), None), (at(seconds=2), None)], agg=Aggregation.MEAN)
    c.check("count still counts null events", nulls.windows[0].count == 2)
    c.check("with_value counts the numbers", nulls.windows[0].with_value == 0)
    c.check("the mean of nulls is undefined", nulls.windows[0].mean is None)
    c.check("the total of nulls is undefined", nulls.windows[0].total is None)
    c.check("an undefined mean prints as a dash", nulls.windows[0].value(Aggregation.MEAN) == "-")

    # -- watermark and lateness ------------------------------------------
    engine = Engine(60 * US, lateness_us=30 * US)
    engine.push(Event(at(seconds=10), 1.0))
    engine.push(Event(at(seconds=50), 1.0))
    engine.push(Event(at(minutes=1, seconds=20), 1.0))
    engine.push(Event(at(seconds=40), 1.0))
    c.check("nothing was rejected yet", engine.report().late == [])
    c.check(
        "the watermark follows event time",
        engine.watermark_us == at(minutes=1, seconds=20) - 30 * US,
    )
    engine.push(Event(at(minutes=2), 1.0))
    first = next(item for item in engine.report().windows if item.window.start_us == at())
    c.check("an event inside the allowance still counts", first.count == 3)

    engine.push(Event(at(minutes=3, seconds=30), 1.0))
    emitted = next(item for item in engine.report().windows if item.window.start_us == at())
    c.check("the watermark closes the window", emitted.final is True)
    engine.push(Event(at(seconds=30), 1.0))
    late = engine.report().late
    c.check("an event past the watermark is late", len(late) == 1)
    c.check("the late report names the window", late[0].window.start_us == at())
    explained = late[0].reason
    c.check("the late report says why", "closed before" in explained or "emitted" in explained)
    unchanged = next(item for item in engine.report().windows if item.window.start_us == at())
    c.check("a late event does not rewrite the answer", unchanged.count == emitted.count)

    flushed = build([(at(seconds=1), 1.0)])
    c.check("a flushed window is marked unconfirmed", flushed.windows[0].final is False)

    gap = build([(at(seconds=5), 1.0), (at(minutes=2, seconds=5), 1.0)])
    c.check("two windows are emitted", len(gap.windows) == 2)
    c.check("the empty window is listed as missing", len(gap.missing()) == 1)
    c.check("the missing window is the middle one", gap.missing()[0].start_us == at(minutes=1))

    sliding = build([(at(seconds=40), 1.0)], hop=30 * US)
    c.check("a sliding event lands in two windows", len(sliding.windows) == 2)
    c.check("and is counted in both", sum(item.count for item in sliding.windows) == 2)

    # -- the report ------------------------------------------------------
    payload = json.loads(json.dumps(report.as_dict()))
    c.check("the report is JSON", payload["aggregation"] == "count")
    c.check("the report lists windows", len(payload["windows"]) == 1)
    c.refuses(
        "an unknown aggregation is refused",
        lambda: Engine(60 * US, aggregation="median"),
        EngineError,
    )
    c.refuses(
        "a negative lateness is refused", lambda: Engine(60 * US, lateness_us=-1), EngineError
    )
    c.refuses("a zero width is refused", lambda: Engine(0), EngineError)
    c.refuses(
        "an inverted covering range is refused",
        lambda: covering(BASE_US, BASE_US - 1, 60 * US),
        WindowError,
    )

    # -- durations -------------------------------------------------------
    c.check("a bare number is seconds", parse_duration("60") == 60 * US)
    c.check("a suffix is honoured", parse_duration("5m") == 300 * US)
    c.check("milliseconds do not collide with seconds", parse_duration("500ms") == 500_000)
    c.check("microseconds work", parse_duration("250us") == 250)

    # -- cli -------------------------------------------------------------
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        events = root / "events.jsonl"
        events.write_text(
            "\n".join(
                [
                    json.dumps({"t": to_iso(at(seconds=1)), "value": 2}),
                    json.dumps({"t": to_iso(at(seconds=2)), "value": 3}),
                ]
            )
            + "\n"
        )
        code = main(["run", "--events", str(events), "--width", "60s", "--agg", "sum"])
        c.check("the cli reads a file", code == EXIT_OK)
        c.check("the file loads two events", len(load(events)) == 2)
        out = root / "report.json"
        main(["run", "--events", str(events), "--json", str(out)])
        written = json.loads(out.read_text())
        c.check("the cli writes its report", written["windows"][0]["count"] == 2)
        code = main(["run", "--events", str(root / "absent.jsonl")])
        c.check("a missing file exits 2", code == EXIT_UNUSABLE)
        late_file = root / "late.jsonl"
        late_file.write_text(
            "\n".join(
                [
                    json.dumps({"t": to_iso(at(minutes=5)), "value": 1}),
                    json.dumps({"t": to_iso(at(seconds=1)), "value": 1}),
                ]
            )
            + "\n"
        )
        c.check("late data exits 1", main(["run", "--events", str(late_file)]) == EXIT_LATE)
        bad = root / "bad.jsonl"
        bad.write_text('{"t": "2026-01-01T00:00:00", "value": 1}\n')
        c.check("a naive timestamp exits 2", main(["run", "--events", str(bad)]) == EXIT_UNUSABLE)

    c.check("the demo tells six stories", len(demo()) == 6)
    c.check("every story has lines", all(lines for _, lines in demo()))
    started = datetime.fromtimestamp(BASE_US / US, UTC)
    c.check("the demo timestamps are minute-aligned", started.minute == 0)

    if c.failures:
        print(f"selftest: {c.failures} of {c.checks} checks failed")
        return 1
    print(f"selftest: {c.checks} checks passed")
    return 0
