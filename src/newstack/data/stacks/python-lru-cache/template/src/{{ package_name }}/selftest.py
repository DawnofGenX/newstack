"""The rules this package keeps, checked in one process and printed as a report."""

from __future__ import annotations

import contextlib
import io

from . import cli as cli_module
from . import simulate
from .cache import POLICIES, CacheError, by_name
from .trace import (
    TRACES,
    TraceError,
    build,
    describe,
    frequency,
    loop_trace,
    mixed_trace,
    scan_trace,
    zipf_trace,
)


class Report:
    """A list of named checks, each of which either held or did not."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []

    def ok(self, name: str, condition: bool, detail: str = "") -> bool:
        if condition:
            self.passed += 1
            return True
        self.failed.append(f"{name}{': ' + detail if detail else ''}")
        return False

    def refuses(self, name: str, kind: type[BaseException], action) -> bool:
        """A call that must raise `kind`, and must not raise anything else."""
        try:
            action()
        except kind:
            self.passed += 1
            return True
        except BaseException as error:
            self.failed.append(
                f"{name}: raised {type(error).__name__}({error}), not {kind.__name__}"
            )
            return False
        self.failed.append(f"{name}: raised nothing")
        return False


@contextlib.contextmanager
def quiet():
    """Silence both streams so a nested command's output does not interleave."""
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        yield sink


def _capacities(report: Report) -> None:
    report.refuses("a zero capacity is refused", CacheError, lambda: by_name("lru")(0))
    report.refuses("a bool capacity is refused", CacheError, lambda: by_name("lru")(True))
    report.refuses("an unknown policy names the ones there are", CacheError, lambda: by_name("mru"))
    try:
        by_name("mru")
    except CacheError as error:
        text = str(error)
        report.ok(
            "the message lists every known policy", all(name in text for name in POLICIES), text
        )
    report.refuses("a non-string key is refused", CacheError, lambda: by_name("lru")(4).access(7))
    report.refuses(
        "a protected share outside (0,1) is refused", CacheError, lambda: by_name("slru")(4, 1.5)
    )


def _policies(report: Report) -> None:
    for name in POLICIES:
        cache = by_name(name)(3)
        first = [cache.access(key) for key in ("a", "b", "c")]
        report.ok(
            f"{name}: the first three accesses miss", first == [False, False, False], str(first)
        )
        report.ok(f"{name}: the cache is full", len(cache) == 3, str(len(cache)))
        report.ok(f"{name}: a repeat hits", cache.access("b") is True)
        report.ok(f"{name}: no eviction until the fourth distinct key", cache.evictions == 0)
        cache.access("d")
        report.ok(
            f"{name}: the fourth distinct key evicts once",
            cache.evictions == 1,
            str(cache.evictions),
        )
        report.ok(f"{name}: it still holds three keys", len(cache) == 3, str(len(cache)))

    fifo = by_name("fifo")(2)
    for key in ("a", "b", "a", "c"):
        fifo.access(key)
    report.ok(
        "fifo forgets the oldest arrival even though it was reused",
        fifo.resident() == {"b", "c"},
        str(sorted(fifo.resident())),
    )

    lru = by_name("lru")(2)
    for key in ("a", "b", "a", "c"):
        lru.access(key)
    report.ok(
        "lru keeps the key that was just used",
        lru.resident() == {"a", "c"},
        str(sorted(lru.resident())),
    )

    clock = by_name("clock")(2)
    for key in ("a", "b", "a", "c"):
        clock.access(key)
    report.ok(
        "clock swept the bits an insertion had set and took the oldest slot",
        clock.resident() == {"b", "c"},
        str(sorted(clock.resident())),
    )
    report.ok("clock counts the slots it swept", clock.scans >= 2, str(clock.scans))

    slru = by_name("slru")(10, 0.8)
    slru.access("hot")
    slru.access("hot")
    report.ok("slru promotes a repeat off probation", slru.promotions == 1, str(slru.promotions))
    for number in range(20):
        slru.access(f"scan-{number}")
    report.ok(
        "slru keeps the promoted key through a scan",
        "hot" in slru.resident(),
        str(sorted(slru.resident())),
    )
    report.ok("slru still holds only its capacity", len(slru) == 10, str(len(slru)))


def _trace(report: Report) -> None:
    for name in TRACES:
        first = build(name, 500, seed=7)
        second = build(name, 500, seed=7)
        report.ok(f"{name}: the same seed builds the same trace", first == second)
        report.ok(f"{name}: the trace has the length asked for", len(first) == 500, str(len(first)))
        report.ok(f"{name}: every access is a string", all(isinstance(key, str) for key in first))
        report.ok(f"{name}: it has a description", bool(describe(name)))

    report.ok(
        "a different seed builds a different zipf trace",
        zipf_trace(500, seed=7) != zipf_trace(500, seed=8),
    )
    report.ok(
        "zipf is skewed",
        frequency(zipf_trace(4000)).most_common(1)[0][1] > 40,
        str(frequency(zipf_trace(4000)).most_common(3)),
    )
    loop = loop_trace(300, 100)
    report.ok("the loop repeats one fixed order", loop[:100] == loop[100:200], str(loop[:3]))
    scan = scan_trace(400, hot=10)
    report.ok(
        "the scan visits fresh keys", len({key for key in scan if key.startswith("scan-")}) > 100
    )
    mixed = mixed_trace(400)
    report.ok(
        "the mixed trace has two namespaces",
        any(key.startswith("loop-") for key in mixed)
        and any(not key.startswith("loop-") for key in mixed),
    )
    report.refuses("an unknown trace name is refused", TraceError, lambda: build("spiral", 10))


def _simulation(report: Report) -> None:
    data = zipf_trace(4000)
    results = simulate.compare(data, 50)
    report.ok("compare returns every policy", len(results) == len(POLICIES), str(len(results)))
    report.ok(
        "every result counted every access", all(result.accesses == len(data) for result in results)
    )
    report.ok(
        "every result reports the policy it ran",
        all(result.policy == name for result, name in zip(results, POLICIES, strict=True)),
    )
    ceiling = simulate.ceiling(data, 50)
    report.ok(
        "no policy beats the ceiling",
        all(result.hit_rate <= ceiling + 1e-12 for result in results),
        f"ceiling {ceiling:.4f} best {max(result.hit_rate for result in results):.4f}",
    )
    report.ok("the ceiling is the share of the top keys", 0.0 < ceiling <= 1.0, f"{ceiling:.4f}")
    report.ok(
        "a bigger capacity never lowers the ceiling",
        simulate.ceiling(data, 100) >= simulate.ceiling(data, 50),
    )
    report.ok(
        "the winner is the best row",
        simulate.winner(results).hit_rate == max(result.hit_rate for result in results),
    )
    report.refuses(
        "an empty trace is refused", simulate.SimulationError, lambda: simulate.run("lru", [], 4)
    )
    report.refuses(
        "an empty comparison is refused", simulate.SimulationError, lambda: simulate.winner([])
    )
    report.refuses(
        "an empty curve is refused",
        simulate.SimulationError,
        lambda: simulate.capacity_curve(data, []),
    )
    report.refuses(
        "a zero capacity curve is refused",
        simulate.SimulationError,
        lambda: simulate.capacity_curve(data, [0]),
    )

    curve = simulate.capacity_curve(data, [10, 50, 200])
    report.ok(
        "the curve returns one row per capacity",
        [row.capacity for row in curve] == [10, 50, 200],
        str([row.capacity for row in curve]),
    )
    rates = [row.hit_rate for row in curve]
    report.ok("more capacity never loses hit rate", rates == sorted(rates), str(rates))

    loop = loop_trace(4000, 200)
    small = simulate.run("lru", loop, 150)
    large = simulate.run("lru", loop, 200)
    report.ok("a loop that does not fit is zero", small.hit_rate == 0.0, f"{small.hit_rate:.4f}")
    report.ok(
        "the loop that fits misses exactly its first pass",
        abs(large.hit_rate - (4000 - 200) / 4000) < 1e-12,
        f"{large.hit_rate:.4f}",
    )

    scan = scan_trace(6000, hot=50)
    lru = simulate.run("lru", scan, 100)
    slru = simulate.run("slru", scan, 100)
    report.ok(
        "a segmented cache survives a scan better than an lru",
        slru.hit_rate > lru.hit_rate * 1.2,
        f"slru {slru.hit_rate:.4f} lru {lru.hit_rate:.4f}",
    )

    zipf = zipf_trace(6000)
    clock = simulate.run("clock", zipf, 100)
    plain = simulate.run("lru", zipf, 100)
    report.ok(
        "clock trails lru by less than two points",
        plain.hit_rate - clock.hit_rate < 0.02,
        f"lru {plain.hit_rate:.4f} clock {clock.hit_rate:.4f}",
    )
    report.ok(
        "clock pays in scans rather than in a list move", clock.scan_work > 0, str(clock.scan_work)
    )
    report.ok("the header names every column", "promotions" in simulate.header(), simulate.header())


def _parser_exit(argv: list[str]) -> int:
    """The exit code argparse would produce, without letting SystemExit out."""
    try:
        cli_module.build_parser().parse_args(argv)
    except SystemExit as error:
        return int(error.code or 0)
    return 0


def _command_line(report: Report) -> None:
    parser = cli_module.build_parser()
    parsed = parser.parse_args(["simulate"])
    report.ok("the parser routes simulate", parsed.handler is cli_module._command_simulate)

    with quiet() as sink:
        code = cli_module.main(
            ["simulate", "--policy", "lru", "--trace", "zipf", "--accesses", "600"]
        )
    report.ok("simulate exits zero", code == 0, sink.getvalue()[-200:])
    report.ok("simulate prints a ceiling line", "ceiling" in sink.getvalue())

    with quiet() as sink:
        code = cli_module.main(
            [
                "simulate",
                "--policy",
                "lru",
                "--trace",
                "zipf",
                "--accesses",
                "600",
                "--min-hit-rate",
                "0.99",
            ]
        )
    report.ok("a missed threshold exits one", code == 1, sink.getvalue()[-200:])
    report.ok("a missed threshold says BREACH", "BREACH" in sink.getvalue())

    with quiet() as sink:
        code = cli_module.main(["compare", "--trace", "scan", "--accesses", "1500"])
    report.ok("compare exits zero", code == 0, sink.getvalue()[-200:])
    report.ok("compare names a best policy", "best" in sink.getvalue())

    with quiet() as sink:
        code = cli_module.main(["curve", "--capacities", "5,25", "--accesses", "600"])
    report.ok("curve exits zero", code == 0, sink.getvalue()[-200:])
    report.ok(
        "curve prints both capacities", "     5" in sink.getvalue() and "    25" in sink.getvalue()
    )

    with quiet():
        code = _parser_exit(["simulate", "--policy", "mru"])
    report.ok("an unknown policy is refused by the parser", code == 2, str(code))

    with quiet():
        code = _parser_exit(["curve", "--capacities", "ten"])
    report.ok("unreadable capacities are refused by the parser", code == 2, str(code))

    with quiet() as sink:
        code = cli_module.main(["demo"])
    report.ok("the demo holds", code == 0, sink.getvalue()[-300:])


def main() -> int:
    report = Report()
    _capacities(report)
    _policies(report)
    _trace(report)
    _simulation(report)
    _command_line(report)
    for failure in report.failed:
        print(f"failed: {failure}")
    print(f"selftest: {report.passed} checks passed")
    return 0 if not report.failed else 1
