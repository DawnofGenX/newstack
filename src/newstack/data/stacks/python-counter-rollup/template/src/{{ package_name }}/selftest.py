"""Checks the arithmetic without pytest, so a checkout can prove itself offline."""

from __future__ import annotations

from collections.abc import Callable

from . import demo, merge, model, rollup

MICROSECONDS = model.MICROSECONDS


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.total = 0

    def ok(self, description: str, condition: bool) -> None:
        self.total += 1
        if condition:
            self.passed += 1
        else:
            print(f"FAIL  {description}")

    def equal(self, description: str, want: object, got: object) -> None:
        self.ok(f"{description} (want {want!r}, got {got!r})", want == got)

    def raises(
        self,
        description: str,
        function: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> None:
        try:
            function(*args, **kwargs)
        except (model.RollupError, ValueError, TypeError):
            self.ok(description, True)
        else:
            self.ok(f"{description} (nothing was raised)", False)


def _readings(pairs: list[tuple[int, int]]) -> list[model.Sample]:
    return [model.Sample(at_us=at * MICROSECONDS, value=value) for at, value in pairs]


def _model_checks(checks: Checks) -> None:
    checks.raises("a bool is not an integer", model.Sample, at_us=True, value=1)
    checks.raises("a negative value is refused", model.Sample, at_us=0, value=-1)
    checks.raises("a window cannot run backwards", model.Window, start_us=10, end_us=10)
    checks.equal("a window is half open", model.Window(0, 10).contains(10), False)
    checks.equal("alignment floors", model.align(19_999_999, 10_000_000), 10_000_000)
    checks.equal("alignment keeps a boundary", model.align(10_000_000, 10_000_000), 10_000_000)
    checks.equal("a width is counted in microseconds", model.seconds(2.5), 2_500_000)
    checks.raises("a zero width is refused", model.seconds, 0)
    checks.equal("an increase is a subtraction", model.delta_for(
        model.Sample(0, 10), model.Sample(1, 25)
    ), (15, False))
    checks.equal("a decrease is a restart", model.delta_for(
        model.Sample(0, 10), model.Sample(1, 3)
    ), (3, True))
    checks.raises(
        "a reading cannot go back in time",
        model.delta_for,
        model.Sample(10, 1),
        model.Sample(5, 2),
    )


def _rollup_checks(checks: Checks) -> None:
    width = 10 * MICROSECONDS
    pieces = rollup.rollup(_readings([(0, 0), (10, 100), (20, 200), (30, 300)]), width, name="r")
    checks.equal("three intervals make three windows", len(pieces), 3)
    checks.equal("the first window is the second heartbeat's", pieces[0].window.start_us, width)
    checks.ok(
        "every window totals one interval",
        all(piece.total == 100 for piece in pieces),
    )
    checks.ok("a steady counter has a steady rate", abs(pieces[0].rate_per_second() - 10) < 1e-9)
    checks.raises(
        "one reading is not a rate",
        model.Rollup(name="r", shard="s", window=model.Window(0, width), total=0,
                     samples=0, resets=0, first_us=0, last_us=0).rate_per_second,
    )
    reset = rollup.rollup(_readings([(0, 500), (10, 600), (20, 20)]), width, name="r")
    checks.equal("a restart reports the new value", reset[1].total, 20)
    checks.equal("a restart is counted", reset[1].resets, 1)
    checks.ok("no window is negative", all(piece.total >= 0 for piece in reset))

    holed = rollup.rollup(
        _readings([(0, 0), (10, 10), (20, 20), (40, 40), (50, 50)]), width, name="r"
    )
    holes = rollup.gaps(holed, width)
    checks.equal("one window is missing", [hole.start_us // MICROSECONDS for hole in holes], [30])
    lonely = rollup.rollup(_readings([(0, 4)]), width, name="r")
    checks.equal("a single reading folds into nothing", lonely, [])
    checks.raises("a single reading has no rate", rollup.rate_per_second, [])
    checks.raises(
        "readings out of order are refused",
        rollup.rollup,
        [model.Sample(10, 1), model.Sample(5, 2)],
        width,
        name="r",
    )
    checks.equal(
        "a rate divides by observed time",
        round(rollup.rate_per_second(holed), 6),
        round(50 / 50.0, 6),
    )


def _merge_checks(checks: Checks) -> None:
    width = 10 * MICROSECONDS
    first = rollup.rollup(_readings([(0, 0), (10, 100)]), width, name="r", shard="a")
    second = rollup.rollup(_readings([(0, 0), (10, 40)]), width, name="r", shard="b")
    once = merge.merge([*first, *second])
    twice = merge.merge([*first, *second, *first])
    checks.equal("two shards make two windows", len(once.rollups), 2)
    checks.equal("a repeat is dropped", twice.repeated, 1)
    checks.equal(
        "a repeat does not change the total",
        sum(piece.total for piece in twice.rollups),
        sum(piece.total for piece in once.rollups),
    )
    checks.equal("combining adds the shards", merge.combine(twice.rollups)[0].total, 140)
    checks.equal("the combined shard is labelled", merge.combine(twice.rollups)[0].shard, "*")
    disagreeing = model.Rollup(
        name="r", shard="a", window=first[0].window, total=999, samples=1, resets=0,
        first_us=0, last_us=10 * MICROSECONDS,
    )
    checks.raises("a disagreeing repeat is refused", merge.merge, [*first, disagreeing])
    payload = [piece.as_dict() for piece in first]
    checks.equal("a rollup survives its own JSON", merge.parse_rollup(payload[0], "x"), first[0])
    checks.raises("a rollup without a window is refused", merge.parse_rollup, {"name": "r"}, "x")


def _demo_checks(checks: Checks) -> None:
    steps = demo.run()
    checks.equal("four scenarios", len(steps), 4)
    for step in steps:
        checks.ok(f"scenario as advertised: {step.scenario}", step.ok)
    checks.ok("the footer counts misses", "0 not as advertised" in demo.render(steps))


GROUPS = (
    ("model", _model_checks),
    ("rollup", _rollup_checks),
    ("merge", _merge_checks),
    ("demo", _demo_checks),
)


def run() -> tuple[int, int]:
    checks = Checks()
    for _name, group in GROUPS:
        group(checks)
    return checks.passed, checks.total
