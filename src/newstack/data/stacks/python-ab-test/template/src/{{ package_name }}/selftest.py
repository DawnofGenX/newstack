"""The rules, checked in process: numbers first, then the command line."""

from __future__ import annotations

import contextlib
import io
import sys

from . import cli
from .rng import Rng, bernoulli
from .sequential import obrien_fleming, simulate, spending
from .srm import check
from .stats import (
    Arm,
    StatsError,
    compare,
    detectable_lift,
    normal_cdf,
    normal_quantile,
    pooled_error,
    sample_per_arm,
    two_sided_p,
    wilson,
)


class Report:
    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []

    def ok(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
        else:
            self.failed.append(f"{name}{': ' + detail if detail else ''}")

    def refuses(self, name: str, kind: type[BaseException], action) -> None:
        try:
            action()
        except kind:
            self.passed += 1
        except BaseException as error:
            self.failed.append(f"{name}: raised {type(error).__name__}, wanted {kind.__name__}")
        else:
            self.failed.append(f"{name}: nothing was raised")


def _numbers(report: Report) -> None:
    report.ok("the 97.5th percentile is 1.96", abs(normal_quantile(0.975) - 1.959964) < 1e-6)
    report.ok("the median is zero", abs(normal_quantile(0.5)) < 1e-9)
    report.ok("the CDF is symmetric", abs(normal_cdf(1.0) + normal_cdf(-1.0) - 1.0) < 1e-12)
    report.ok("a two-sided p at zero is one", abs(two_sided_p(0.0) - 1.0) < 1e-12)
    report.ok("a two-sided p at 1.96 is about 5%", abs(two_sided_p(1.959964) - 0.05) < 1e-4)
    report.refuses("a quantile of zero is refused", StatsError, lambda: normal_quantile(0.0))

    interval = wilson(50, 100)
    report.ok("wilson around one half is the textbook interval",
              abs(interval.low - 0.4038) < 1e-4 and abs(interval.high - 0.5962) < 1e-4,
              interval.text())
    report.ok("wilson stays inside 0..1 at the edges", wilson(0, 20).low >= 0.0)
    report.ok("a zero count has a non-zero upper bound", wilson(0, 20).high > 0.0)

    small = compare(Arm("control", 100, 1000), Arm("treatment", 130, 1000))
    report.ok("a 30% lift on a thousand is significant", small.significant(), small.lines()[-1])
    report.ok("the direction is upward", small.direction() == "higher")
    report.ok("the interval excludes zero", not small.interval.contains(0.0), small.interval.text())
    report.ok("the lift is the difference over the baseline", abs(small.lift - 0.30) < 1e-9)

    flat = compare(Arm("control", 100, 1000), Arm("treatment", 100, 1000))
    report.ok("identical arms are indistinguishable", flat.direction() == "indistinguishable")
    report.ok("identical arms have p one", abs(flat.p_value - 1.0) < 1e-12)

    report.ok("the pooled error is what the test divides by",
              abs(pooled_error(Arm("a", 100, 1000), Arm("b", 130, 1000)) - 0.0138) < 1e-3)
    report.refuses("alpha must be a probability", StatsError,
                   lambda: compare(Arm("a", 1, 10), Arm("b", 1, 10), alpha=1.5))
    report.refuses("impossible conversions are refused", StatsError, lambda: Arm("a", 11, 10))
    report.refuses("an arm with no visitors is refused", StatsError, lambda: Arm("a", 0, 0))
    report.refuses("an arm needs a name", StatsError, lambda: Arm("", 1, 10))
    report.refuses("an arm text without a slash is refused", StatsError,
                   lambda: Arm.from_text("control=10"))
    parsed = Arm.from_text("control=100/1000")
    report.ok("an arm parses from text", parsed == Arm("control", 100, 1000))

    report.ok("the sample size for a 5% lift on 10% is in the expected range",
              50_000 < sample_per_arm(0.10, 0.05) < 65_000, str(sample_per_arm(0.10, 0.05)))
    report.ok("a bigger lift needs fewer visitors",
              sample_per_arm(0.10, 0.20) < sample_per_arm(0.10, 0.10))
    report.refuses("a lift of zero has no sample size", StatsError,
                   lambda: sample_per_arm(0.10, 0.0))
    report.ok("the detectable lift shrinks as the sample grows",
              detectable_lift(0.10, 40_000) < detectable_lift(0.10, 10_000))
    report.ok("the sample size and the detectable lift agree",
              detectable_lift(0.10, sample_per_arm(0.10, 0.05)) < 0.0501)


def _mismatch(report: Report) -> None:
    bad = check(Arm("control", 5000, 102_000), Arm("treatment", 5000, 100_000))
    report.ok("a one percent imbalance is caught", bad.mismatched, f"p={bad.p_value:.2e}")
    good = check(Arm("control", 5000, 100_200), Arm("treatment", 5000, 100_000))
    report.ok("a balanced split is plausible", not good.mismatched, f"p={good.p_value:.3f}")
    report.ok("the chi-square of an exactly even split is zero",
              check(Arm("a", 1, 500), Arm("b", 1, 500)).chi_square < 1e-12)
    report.refuses("a split outside 0..1 is refused", StatsError,
                   lambda: check(Arm("a", 1, 10), Arm("b", 1, 10), split=1.0))


def _peeking(report: Report) -> None:
    boundary = obrien_fleming(0.05, 5)
    report.ok("the last look is the plain boundary", abs(boundary.at(5) - 1.959964) < 1e-5)
    report.ok("the first look is much stricter", boundary.at(1) > 3.0, f"{boundary.at(1):.3f}")
    falling = list(boundary.critical) == sorted(boundary.critical, reverse=True)
    report.ok("the critical values fall", falling)
    report.ok("the spending sums to more than alpha",
              sum(spending(0.05, 5)) > 0.05, f"{sum(spending(0.05, 5)):.4f}")
    report.refuses("a boundary needs a look", StatsError, lambda: obrien_fleming(0.05, 0))

    world = simulate(trials=200, visitors=1000, looks=5, seed=3)
    report.ok("peeking crosses more often than one look",
              world.peeking_crossings > world.fixed_crossings,
              f"{world.peeking_crossings} against {world.fixed_crossings}")
    report.ok("the boundary is closer to alpha than the flat line",
              world.rate(world.guarded_crossings) < world.rate(world.peeking_crossings))
    report.ok("the same seed reproduces the same worlds",
              simulate(trials=200, visitors=1000, looks=5, seed=3).peeking_crossings
              == world.peeking_crossings)
    report.refuses("more looks than visitors is refused", StatsError,
                   lambda: simulate(visitors=5, looks=10, trials=2))


def _generator(report: Report) -> None:
    first = Rng(7)
    second = Rng(7)
    report.ok("the generator is reproducible",
              [first.next_u64() for _ in range(3)] == [second.next_u64() for _ in range(3)])
    report.ok("different seeds differ", Rng(7).next_u64() != Rng(8).next_u64())
    draws = Rng(1)
    samples = [draws.random() for _ in range(2000)]
    report.ok("the draws stay in 0..1", all(0.0 <= value < 1.0 for value in samples))
    report.ok("the mean of the draws is near a half", abs(sum(samples) / len(samples) - 0.5) < 0.03)
    report.ok("bernoulli counts within a wide band",
              150 < bernoulli(Rng(2), 1000, 0.2) < 250, str(bernoulli(Rng(2), 1000, 0.2)))


def _command_line(report: Report) -> None:
    def run(*argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = cli.main(list(argv))
            except SystemExit as exit_code:
                code = int(exit_code.code or 0)
        return code, out.getvalue(), err.getvalue()

    code, out, _ = run("compare", "--control", "control=100/1000",
                       "--treatment", "treatment=130/1000")
    report.ok("compare exits zero", code == cli.EXIT_OK, out)
    report.ok("compare prints the verdict", "higher" in out)
    code, out, _ = run("compare", "--control", "control=100/1000",
                       "--treatment", "treatment=100/1000", "--json")
    report.ok("compare --json prints a document", code == 0 and '"significant": false' in out, out)
    code, _, err = run("compare", "--control", "control=130/1000",
                       "--treatment", "treatment=100/1000")
    report.ok("a worse treatment is still an exit zero", code == cli.EXIT_OK)

    code, out, _ = run("srm", "--control", "control=5000/102000",
                       "--treatment", "treatment=5000/100000")
    report.ok("a mismatch exits one", code == cli.EXIT_REFUSED, out)
    code, out, _ = run("srm", "--control", "control=5000/100200",
                       "--treatment", "treatment=5000/100000")
    report.ok("a plausible split exits zero", code == cli.EXIT_OK, out)

    code, out, _ = run("power", "--baseline", "0.10", "--lift", "0.05")
    report.ok("power prints a per-arm number", code == 0 and "per arm" in out, out)
    code, out, _ = run("power", "--baseline", "0.10", "--lift", "0.05", "--visitors", "20000")
    report.ok("power names the effect a small sample could catch", "would be caught" in out)

    code, out, _ = run("peeking", "--trials", "100", "--visitors", "1000", "--looks", "5")
    report.ok("peeking runs and reports a verdict", code == 0 and "verdict" in out, out)
    code, out, _ = run("peeking", "--trials", "100", "--json")
    report.ok("peeking --json prints rates", code == 0 and '"every_look"' in out, out)

    code, _, err = run("compare", "--control", "control=10", "--treatment", "treatment=10/10")
    report.ok("a malformed arm is a usage error", code == cli.EXIT_UNUSABLE, err)
    report.ok("the usage error names the problem", "whole numbers" in err, err)
    code, _, err = run("compare", "--control", "control=11/10", "--treatment", "treatment=1/10")
    report.ok("an impossible arm is a usage error", code == cli.EXIT_UNUSABLE, err)

    code, out, _ = run("demo")
    report.ok("the demo holds every story", code == 0 and out.count("-> holds") == 6, out[-200:])
    parsed = cli.build_parser().parse_args(["selftest"])
    report.ok("the parser routes selftest without running it",
              parsed.handler is cli._command_selftest)


def main() -> int:
    report = Report()
    _numbers(report)
    _mismatch(report)
    _peeking(report)
    _generator(report)
    _command_line(report)
    for failure in report.failed:
        print(f"FAILED {failure}", file=sys.stderr)
    print(f"selftest: {report.passed} checks passed")
    return 0 if not report.failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
