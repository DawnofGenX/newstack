"""The selftest: every claim the README makes, checked here."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import cli as cli_module
from . import demo
from .explain import decide
from .ranges import RangeError, intersect, parse_range
from .version import VersionError, compare, parse

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"


@dataclass
class Report:
    checks: int = 0
    failures: list[str] = field(default_factory=list)
    ok: bool = field(default=True)

    def expect(self, claim: str, held: bool) -> None:
        self.checks += 1
        if not held:
            self.ok = False
            self.failures.append(claim)

    def refuse(self, claim: str, call, expected) -> None:
        self.checks += 1
        try:
            call()
        except expected:
            return
        except Exception as error:
            self.ok = False
            message = f"{claim}: raised {type(error).__name__}, wanted {expected.__name__}"
            self.failures.append(message)
            return
        self.ok = False
        self.failures.append(f"{claim}: nothing was raised")


def _version_section(report: Report) -> None:
    report.expect("1.10.0 is above 1.9.0", parse("1.10.0") > parse("1.9.0"))
    report.expect(
        "prereleases sort below the release",
        parse("1.0.0-rc.1") < parse("1.0.0"),
    )
    report.expect(
        "numeric prerelease identifiers are numbers",
        parse("1.0.0-alpha.9") < parse("1.0.0-alpha.10"),
    )
    report.expect(
        "numeric identifiers sort below alphanumeric ones",
        parse("1.0.0-1") < parse("1.0.0-alpha"),
    )
    report.expect(
        "build metadata is not precedence",
        parse("1.0.0+left") == parse("1.0.0+right"),
    )
    report.expect("compare reports equality", compare(parse("2.0.0"), parse("2.0.0")) == 0)
    report.refuse("a leading zero is refused", lambda: parse("1.02.3"), VersionError)
    report.refuse("a missing patch is refused", lambda: parse("1.2"), VersionError)
    report.refuse("an empty prerelease is refused", lambda: parse("1.2.3-"), VersionError)
    report.refuse(
        "a numeric prerelease with a leading zero is refused",
        lambda: parse("1.2.3-01"),
        VersionError,
    )


def _caret_section(report: Report) -> None:
    cases = [
        ("^1.2.3", "1.2.3", "2.0.0", "1.9.9", "1.2.2"),
        ("^0.2.3", "0.2.3", "0.3.0", "0.2.9", "0.3.0"),
        ("^0.0.3", "0.0.3", "0.0.4", "0.0.3", "0.0.4"),
        ("^0.0", "0.0.0", "0.1.0", "0.0.9", "0.1.0"),
        ("^0", "0.0.0", "1.0.0", "0.9.9", "1.0.0"),
    ]
    for text, low, high, inside, outside in cases:
        chosen = parse_range(text)
        report.expect(f"{text} starts at {low}", chosen.allows(parse(low)))
        report.expect(f"{text} refuses {high}", not chosen.allows(parse(high)))
        report.expect(f"{text} allows {inside}", chosen.allows(parse(inside)))
        report.expect(f"{text} refuses {outside}", not chosen.allows(parse(outside)))


def _partial_section(report: Report) -> None:
    report.expect("1.2 allows 1.2.99", parse_range("1.2").allows(parse("1.2.99")))
    report.expect("1.2 refuses 1.3.0", not parse_range("1.2").allows(parse("1.3.0")))
    report.expect("1 allows 1.99.99", parse_range("1").allows(parse("1.99.99")))
    report.expect("1 refuses 2.0.0", not parse_range("1").allows(parse("2.0.0")))
    report.expect(">1.2 starts at 1.3.0", parse_range(">1.2").allows(parse("1.3.0")))
    report.expect(">1.2 refuses 1.2.99", not parse_range(">1.2").allows(parse("1.2.99")))
    report.expect("<=1.2 allows 1.2.99", parse_range("<=1.2").allows(parse("1.2.99")))
    report.expect("<=1.2 refuses 1.3.0", not parse_range("<=1.2").allows(parse("1.3.0")))
    report.expect("* allows 7.3.1", parse_range("*").allows(parse("7.3.1")))
    report.expect("1.2.x allows 1.2.7", parse_range("1.2.x").allows(parse("1.2.7")))
    report.expect("1.2.x refuses 1.3.0", not parse_range("1.2.x").allows(parse("1.3.0")))
    report.refuse(
        "a bound with no version is refused",
        lambda: parse_range(">"),
        RangeError,
    )
    report.refuse("an empty range is refused", lambda: parse_range("   "), RangeError)
    report.refuse("an empty || arm is refused", lambda: parse_range("1.2 || "), RangeError)
    report.refuse("a bad field is refused", lambda: parse_range("1.two"), RangeError)


def _hyphen_section(report: Report) -> None:
    hyphen = parse_range("1.2 - 2.3.4")
    report.expect("the hyphen start is 1.2.0", hyphen.allows(parse("1.2.0")))
    report.expect("the hyphen start excludes 1.1.9", not hyphen.allows(parse("1.1.9")))
    report.expect("the hyphen end is inclusive", hyphen.allows(parse("2.3.4")))
    report.expect("the hyphen end stops at 2.3.5", not hyphen.allows(parse("2.3.5")))
    partial_end = parse_range("1.2.3 - 2.3")
    report.expect("a partial end covers its whole interval", partial_end.allows(parse("2.3.9")))
    report.expect("a partial end stops at 2.4.0", not partial_end.allows(parse("2.4.0")))
    union = parse_range("~1.4 || ^2.0")
    report.expect(
        "two arms are two intervals",
        union.allows(parse("1.4.0")) and union.allows(parse("2.0.0")),
    )
    report.expect("the gap between arms is a gap", not union.allows(parse("1.9.0")))


def _prerelease_section(report: Report) -> None:
    report.expect(
        "a caret range does not opt into prereleases",
        not parse_range("^1.2.0").allows(parse("1.3.0-beta")),
    )
    report.expect(
        "an exact prerelease allows itself",
        parse_range("1.3.0-beta").allows(parse("1.3.0-beta")),
    )
    report.expect(
        "a named prerelease gate allows the same core",
        parse_range(">=1.3.0-beta <2").allows(parse("1.3.0-beta.2")),
    )
    report.expect(
        "the gate does not leak to another core",
        not parse_range(">=1.3.0-beta <2").allows(parse("1.4.0-rc.1")),
    )
    report.expect(
        "a release above a named prerelease is allowed",
        parse_range(">=1.3.0-beta <2").allows(parse("1.3.0")),
    )


def _intersect_section(report: Report) -> None:
    narrow = intersect(parse_range("^1.2.3"), parse_range(">=1.4.0 <1.5.0"))
    report.expect("the overlap exists", narrow is not None)
    report.expect(
        "the overlap is the tighter interval",
        narrow is not None
        and narrow.allows(parse("1.4.0"))
        and not narrow.allows(parse("1.5.0"))
        and not narrow.allows(parse("1.3.9")),
    )
    report.expect(
        "disjoint ranges are empty",
        intersect(parse_range("^1.0"), parse_range("^2.0")) is None,
    )
    report.expect(
        "touching exclusive bounds are empty",
        intersect(parse_range("<1.0.0"), parse_range(">=1.0.0")) is None,
    )
    both = intersect(parse_range(">=1.0.0"), parse_range("<=1.0.0"))
    report.expect(
        "touching inclusive bounds keep the point",
        both is not None and both.allows(parse("1.0.0")),
    )
    forward = intersect(parse_range("1.2 - 2.0"), parse_range("^1.5"))
    backward = intersect(parse_range("^1.5"), parse_range("1.2 - 2.0"))
    report.expect("both intersections exist", forward is not None and backward is not None)
    report.expect(
        "intersection is commutative",
        forward is not None
        and backward is not None
        and sorted(arm.bound_text() for arm in forward.arms)
        == sorted(arm.bound_text() for arm in backward.arms),
    )


def _explain_section(report: Report) -> None:
    decision = decide(parse("1.5.0"), parse_range("~1.4 || ^2.0"))
    report.expect("the version is refused", not decision.ok)
    report.expect("both arms are explained", len(decision.reasons) == 2)
    report.expect(
        "the reason names the bound",
        "upper bound" in decision.reasons[0] or "below the lower" in decision.reasons[1],
    )
    allowed = decide(parse("1.4.2"), parse_range("~1.4 || ^2.0"))
    report.expect("an accepted version names its arm", allowed.arm == 1)
    report.expect("the verdict says which arm", "arm 1" in allowed.verdict())
    beta = decide(parse("1.3.0-beta"), parse_range("^1.2.0"))
    report.expect("a prerelease refusal says why", "prerelease" in beta.reasons[0])


def _command_line_section(report: Report) -> None:
    parser = cli_module.build_parser()
    routes = [
        (["parse", "^1.0"], cli_module._command_parse),
        (["satisfy", "1.0.0", "--range", "*"], cli_module._command_satisfy),
        (["intersect", "a", "b"], cli_module._command_intersect),
        (["sort", "--input", "x"], cli_module._command_sort),
        (["demo"], cli_module._command_demo),
        (["selftest"], cli_module._command_selftest),
    ]
    for argv, handler in routes:
        report.expect(f"{argv[0]} is routed", parser.parse_args(argv).handler is handler)
    fixture = FIXTURES / "versions.txt"
    report.expect("the fixture exists", fixture.exists())
    listed = [
        parse(line.strip())
        for line in fixture.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    report.expect("the fixture holds versions", len(listed) >= 8)
    report.expect("the fixture is not already sorted", listed != sorted(listed))


def _stories_section(report: Report) -> None:
    lines = demo.render_stories()
    report.expect("every story holds", lines[-1] == "stories      6 of 6 hold")
    report.expect("six stories are printed", len(demo.stories()) == 6)
    report.expect("no story is marked broken", "BROKEN" not in "\n".join(lines))
    report.expect("the run reports success", demo.run() == 0)


def run() -> int:
    report = Report()
    _version_section(report)
    _caret_section(report)
    _partial_section(report)
    _hyphen_section(report)
    _prerelease_section(report)
    _intersect_section(report)
    _explain_section(report)
    _command_line_section(report)
    _stories_section(report)
    if report.ok:
        print(f"selftest: {report.checks} checks passed, 0 failed")
        return 0
    for failure in report.failures:
        print(f"FAIL {failure}")
    print(f"selftest: {len(report.failures)} failed of {report.checks}")
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
