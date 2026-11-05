"""Prove the rules, in one process, without a test runner."""

from __future__ import annotations

import io
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from . import cli, lockfile, ranges, resolver, versions
from .index import parse_index

CHECKS = 0
FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if condition:
        return
    FAILURES.append(f"{name}{(': ' + detail) if detail else ''}")


def refuses(name: str, callable_, kind: type[BaseException]) -> str:
    try:
        callable_()
    except kind as error:
        check(name, True)
        return str(error)
    except Exception as error:  # any other error is a failed check
        check(name, False, f"raised {type(error).__name__} instead of {kind.__name__}")
        return ""
    check(name, False, "did not raise")
    return ""


DIAMOND = {
    "web": {
        "2.0.0": {"shared": "^1.2.0"},
        "2.1.0": {"shared": "^2.0.0"},
        "2.1.1": {"shared": "^2.0.0"},
    },
    "cli": {"1.0.0": {"shared": "^1.0.0"}, "1.1.0": {"shared": "^1.0.0"}},
    "shared": {"1.2.0": {}, "1.4.0": {}, "2.0.0": {}, "3.0.0-rc.1": {}},
    "tiny": {"0.2.3": {}, "0.3.0": {}},
}


def _index():
    return parse_index({"packages": DIAMOND})


def _allows(text: str, candidate: str) -> bool:
    return ranges.parse_range(text).allows(versions.parse(candidate))


def _versions() -> None:
    version = versions.parse("1.2.3")
    check(
        "a version keeps its three numbers",
        (version.major, version.minor, version.patch) == (1, 2, 3),
    )
    check("a version round trips through text", version.text == "1.2.3")

    order = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
    ]
    parsed = [versions.parse(text) for text in order]
    check("the specification's ordering example sorts as printed", parsed == sorted(parsed))
    check("and does not sort as reversed text", parsed != list(reversed(parsed)))
    check(
        "numeric identifiers compare as numbers",
        versions.parse("1.0.0-beta.11") > versions.parse("1.0.0-beta.2"),
    )
    check(
        "a release outranks its own prerelease",
        versions.parse("1.0.0") > versions.parse("1.0.0-rc.1"),
    )
    check(
        "build metadata is not comparable",
        versions.parse("1.0.0+a") == versions.parse("1.0.0+b"),
    )
    check(
        "but build metadata is still kept for display",
        versions.parse("1.0.0+a").text == "1.0.0+a",
    )
    leading = refuses(
        "a leading zero in a prerelease is refused",
        lambda: versions.parse("1.0.0-01"),
        versions.VersionError,
    )
    check("and the message says why", "leading zero" in leading, leading)
    refuses("a two-part version is refused", lambda: versions.parse("1.2"), versions.VersionError)
    check("try_parse returns None instead of raising", versions.try_parse("nope") is None)


def _ranges() -> None:
    check("caret allows the whole major", _allows("^1.2.3", "1.9.9"))
    check("caret refuses the next major", not _allows("^1.2.3", "2.0.0"))
    check("caret refuses an older patch", not _allows("^1.2.3", "1.2.2"))
    check(
        "caret at zero freezes the minor",
        _allows("^0.2.3", "0.2.9") and not _allows("^0.2.3", "0.3.0"),
    )
    check(
        "caret at zero-zero freezes the patch",
        _allows("^0.0.3", "0.0.3") and not _allows("^0.0.3", "0.0.4"),
    )
    check(
        "a bare caret zero means before one point oh",
        _allows("^0", "0.9.9") and not _allows("^0", "1.0.0"),
    )
    check(
        "tilde freezes the minor when a patch is written",
        _allows("~1.2.3", "1.2.9") and not _allows("~1.2.3", "1.3.0"),
    )
    check(
        "tilde with major and minor freezes the minor",
        _allows("~1.2", "1.2.7") and not _allows("~1.2", "1.3.0"),
    )
    check(
        "tilde with only a major freezes the major",
        _allows("~1", "1.9.9") and not _allows("~1", "2.0.0"),
    )
    check("a prerelease does not satisfy a lower bound alone", not _allows(">=1.0.0", "1.1.0-rc.1"))
    check("a caret does not pull the next major's prerelease", not _allows("^2.0.0", "3.0.0-rc.1"))
    check("a wildcard does not match a prerelease", not _allows("*", "1.0.0-rc.1"))
    check("a range that names the prerelease takes it", _allows(">=3.0.0-rc.1", "3.0.0-rc.1"))
    check("a caret on a prerelease keeps that line", _allows("^3.0.0-rc.1", "3.0.0-rc.2"))
    check(
        "comparator sets are conjunctions",
        _allows(">=1.0.0 <2.0.0", "1.4.0") and not _allows(">=1.0.0 <2.0.0", "2.0.0"),
    )
    check(
        "unions are disjunctions",
        _allows("1.0.0 || >=2.0.0", "2.5.0") and not _allows("1.0.0 || >=2.0.0", "1.5.0"),
    )
    check(
        "a partial version is padded, not guessed",
        _allows(">=1.2", "1.2.0") and not _allows(">=1.2", "1.1.9"),
    )
    empty = refuses(
        "an empty range is refused", lambda: ranges.parse_range("  "), ranges.RangeError
    )
    check("and says it is ambiguous", "ambiguous" in empty, empty)
    refused = refuses(
        "an unreadable range is refused", lambda: ranges.parse_range("banana"), ranges.RangeError
    )
    check("and names the text", "banana" in refused, refused)


def _index_rules() -> None:
    index = _index()
    candidates = index.candidates("shared", ranges.parse_range("^1.0.0"))
    check(
        "candidates come back highest first",
        [item.text for item in candidates] == ["1.4.0", "1.2.0"],
    )
    missing = refuses(
        "a missing dependency is refused at load",
        lambda: parse_index({"packages": {"web": {"1.0.0": {"shared": "^1.0.0"}}}}),
        ValueError,
    )
    check("and names the release that asks", "web 1.0.0 depends on 'shared'" in missing, missing)
    twice = refuses(
        "two spellings of one version are refused",
        lambda: parse_index({"packages": {"shared": {"1.0.0": {}, "1.0.0+b1": {}}}}),
        ValueError,
    )
    check("and says why", "two spellings" in twice, twice)
    refuses(
        "a package with no versions is refused",
        lambda: parse_index({"packages": {"shared": {}}}),
        ValueError,
    )


def _resolver_rules() -> None:
    index = _index()
    resolution = resolver.resolve(index, {"web": "^2.0.0", "cli": "^1.0.0"})
    check("the greedy choice is abandoned", resolution.version("web").text == "2.0.0")
    check(
        "and the shared package settles on the surviving line",
        resolution.version("shared").text == "1.4.0",
    )
    check("every package gets exactly one version", resolution.count == 3)

    problem = refuses(
        "an impossible pair raises instead of guessing",
        lambda: resolver.resolve(index, {"web": "^2.1.0", "cli": "^1.0.0"}),
        resolver.ResolveError,
    )
    check(
        "the message names both ranges",
        "shared ^2.0.0" in problem and "^1.0.0" in problem,
        problem,
    )

    reversed_roots = resolver.resolve(index, {"cli": "^1.0.0", "web": "^2.0.0"})
    check(
        "root order does not change the answer",
        reversed_roots.as_dict()["packages"] == resolution.as_dict()["packages"],
    )
    why = "\n".join(resolution.why("shared"))
    check(
        "why lists a requirement from every parent", "web@2.0.0" in why and "cli@1.1.0" in why, why
    )

    locked = {"web": versions.parse("2.0.0"), "shared": versions.parse("1.2.0")}
    kept = resolver.resolve(index, {"web": "^2.0.0"}, locked=locked)
    check("a lock is preferred while it fits", kept.version("shared").text == "1.2.0")
    upgraded = resolver.resolve(
        index, {"shared": "^2.0.0"}, locked={"shared": versions.parse("1.2.0")}
    )
    check("a lock that does not fit is replaced", upgraded.version("shared").text == "2.0.0")

    cycle = parse_index(
        {
            "packages": {
                "left": {"1.0.0": {"right": "^1.0.0"}},
                "right": {"1.0.0": {"left": "^1.0.0"}},
            }
        }
    )
    check("a cycle terminates", resolver.resolve(cycle, {"left": "^1.0.0"}).count == 2)
    guard = refuses(
        "the search budget stops a runaway",
        lambda: resolver.resolve(index, {"web": "^2.0.0"}, limit=1),
        resolver.ResolveError,
    )
    check("and the message says it gave up", "gave up" in guard, guard)
    unknown = refuses(
        "an unknown root is an input error",
        lambda: resolver.resolve(index, {"nope": "^1.0.0"}),
        resolver.ResolveError,
    )
    check("and names the package", "not published" in unknown, unknown)


def _lock_rules() -> None:
    index = _index()
    resolution = resolver.resolve(index, {"web": "^2.0.0"})
    text = lockfile.render(resolution)
    check("a lockfile ends with a newline", text.endswith("\n"))
    check("a lockfile is sorted by package", text.index('"shared"') < text.index('"web"'))

    with tempfile.TemporaryDirectory() as directory:
        path = lockfile.write(Path(directory) / "deps.lock.json", resolution)
        read_back = lockfile.read(path)
        check(
            "a lockfile round trips through disk",
            {name: version.text for name, version in read_back.packages.items()}
            == {"shared": "2.0.0", "web": "2.1.1"},
        )
        check(
            "a current lock has no drift", lockfile.audit(index, read_back, {"web": "^2.0.0"}) == []
        )

    future = refuses(
        "a future lockfile format is refused",
        lambda: lockfile.parse_lock({"version": 99}),
        lockfile.LockError,
    )
    check("and says it will not guess", "refusing to guess" in future, future)
    refuses(
        "an empty lockfile is refused",
        lambda: lockfile.parse_lock({"version": 1, "packages": {}}),
        lockfile.LockError,
    )

    stale = lockfile.Lock({"web": versions.parse("2.0.0"), "gone": versions.parse("1.0.0")})
    drift = lockfile.audit(index, stale, {"web": "^2.0.0"})
    check("a locked package nobody needs is drift", "gone" in [item.package for item in drift])
    excluded = lockfile.Lock({"web": versions.parse("1.0.0")})
    reasons = "\n".join(item.line() for item in lockfile.audit(index, excluded, {"web": "^2.0.0"}))
    check(
        "a locked version the requirements exclude is drift",
        "requirements select" in reasons,
        reasons,
    )


def _cli_rules() -> None:
    def run(argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(argv)
        return code, out.getvalue(), err.getvalue()

    code, out, _ = run(["resolve", "--root", "web=^2.0.0", "--root", "cli=^1.0.0"])
    check("resolve exits zero", code == cli.EXIT_OK)
    check("resolve prints the surviving web", "web                2.0.0" in out, out)
    check("resolve counts its work", "resolved 3 package(s)" in out, out)

    code, out, err = run(["resolve", "--root", "web=^2.1.0", "--root", "cli=^1.0.0"])
    check("a conflict exits one", code == cli.EXIT_UNSATISFIED)
    check("a conflict prints nothing to stdout", out == "")
    check("a conflict explains itself on stderr", "no resolution exists" in err, err)

    code, _, err = run(["resolve", "--root", "web=banana"])
    check("an unreadable range exits two", code == cli.EXIT_UNUSABLE)
    code, _, err = run(["resolve", "--root", "web"])
    check("a malformed root exits two", code == cli.EXIT_UNUSABLE and "name=RANGE" in err)
    code, _, _ = run(["why", "--root", "web=^2.0.0", "tiny"])
    check("why refuses a package outside the resolution", code == cli.EXIT_UNUSABLE)
    code, out, _ = run(["demo"])
    check("the demo runs", code == cli.EXIT_OK)
    check("and tells its six stories", "6. a lock keeps the tree" in out, out[:200])


def main() -> int:
    _versions()
    _ranges()
    _index_rules()
    _resolver_rules()
    _lock_rules()
    _cli_rules()
    if FAILURES:
        print(f"selftest: {len(FAILURES)} of {CHECKS} checks failed")
        for failure in FAILURES:
            print(f"  {failure}")
        return 1
    print(f"selftest: {CHECKS} checks passed")
    return 0
