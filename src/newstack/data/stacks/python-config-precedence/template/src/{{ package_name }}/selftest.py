"""Offline checks for the parts that are easy to get subtly wrong.

Nothing here touches the filesystem outside ``fixtures/`` and nothing reads the
real environment, so the result is the same on the developer's laptop and in CI.
Run it with the ``selftest`` subcommand.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import resolve as resolver
from . import sources, spec
from .spec import ConfigError

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            return
        self.failed += 1
        suffix = f" ({detail})" if detail else ""
        print(f"FAIL {name}{suffix}")

    def equal(self, name: str, want: Any, got: Any) -> None:
        self.ok(name, want == got, f"want {want!r}, got {got!r}")

    def raises(self, name: str, fragment: str, call) -> None:
        try:
            call()
        except ConfigError as error:
            self.ok(name, fragment in str(error), f"{fragment!r} not in {str(error)!r}")
            return
        except Exception as error:  # a wrong exception is a failure too
            self.ok(name, False, f"raised {type(error).__name__}: {error}")
            return
        self.ok(name, False, "nothing was raised")


def _parsing(checks: Checks) -> None:
    def parsed(name: str, raw: Any, where: str = "env X") -> Any:
        return sources.parse(spec.get(name), raw, where)

    checks.equal("integer from text", 9100, parsed("server.port", "9100"))
    checks.raises(
        "underscored integer is refused",
        "not numbers anyone types",
        lambda: parsed("server.port", "1_000"),
    )
    checks.equal("boolean yes", True, parsed("features.rate_limit", "yes"))
    checks.equal("boolean off", False, parsed("features.rate_limit", "OFF"))
    checks.raises(
        "boolean is not int()",
        "expected a boolean",
        lambda: parsed("features.rate_limit", "2"),
    )
    checks.equal("duration ms", 2500, parsed("server.timeout", "2500ms"))
    checks.equal("duration minutes", 120_000, parsed("auth.token_ttl", "2m"))
    checks.raises(
        "unitless duration is refused",
        "expected a duration",
        lambda: parsed("server.timeout", "5"),
    )
    checks.equal(
        "list from env text", ("a", "b"), parsed("features.allowed_origins", "a, b")
    )
    checks.equal("empty list text", (), parsed("features.allowed_origins", ""))
    checks.raises(
        "list with a hole",
        "empty item",
        lambda: parsed("features.allowed_origins", "a,,b"),
    )
    checks.equal("choice is case-insensitive", "warning", parsed("log.level", "WARNING"))
    checks.raises(
        "choice outside the set",
        "expected one of",
        lambda: parsed("log.level", "verbose"),
    )
    checks.raises(
        "upper bound is enforced",
        "above the maximum",
        lambda: parsed("server.port", "70000", "file broken.toml"),
    )


def _layers(checks: Checks) -> None:
    layer, problems = sources.from_file(FIXTURES / "config.toml")
    checks.equal("file problems", [], problems)
    checks.equal("file value", (9100, f"file {FIXTURES / 'config.toml'}"), layer["server.port"])
    checks.ok("file flattens tables", "db.pool_size" in layer)

    layer, problems = sources.from_file(FIXTURES / "broken.toml")
    checks.ok("unknown file key is a typo", any("tymeout" in problem for problem in problems))
    checks.ok("broken file still yields values", "server.port" in layer)

    layer, problems = sources.from_env({"APP_SERVER__PORT": "9200", "PATH": "/bin"}, "APP")
    checks.equal("env reads the prefixed variable", "9200", layer["server.port"][0])
    checks.equal("env ignores unreadable ones", ["server.port"], sorted(layer))
    checks.equal("env problems", [], problems)

    _, problems = sources.from_env({"APP_SERVER_PORT": "9200"}, "APP")
    checks.ok(
        "single underscore is reported",
        any("double underscore" in problem for problem in problems),
        str(problems),
    )

    layer, problems = sources.from_flags(["log.level=debug", "novalue", "nope.key=1"])
    checks.equal("flag value", ("debug", "flag --set log.level"), layer["log.level"])
    checks.equal("flag problems", 2, len(problems))

    checks.raises(
        "missing file",
        "cannot read",
        lambda: sources.load_file(FIXTURES / "does-not-exist.toml"),
    )
    checks.raises(
        "unknown setting",
        "unknown setting",
        lambda: spec.get("server.prot"),
    )


def _resolution(checks: Checks) -> None:
    config = FIXTURES / "config.toml"
    signed = {"APP_AUTH__SIGNING_KEY": "s3cret"}

    plain = resolver.resolve(config=config, environ=signed)
    checks.ok("resolution is clean", plain.ok, str(plain.problems))
    checks.equal("file beats the schema", 9100, plain.get("server.port").value)
    checks.equal("file provenance", "file", plain.get("server.port").source)
    checks.equal("a non-secret is never masked", 9100, plain.get("server.port").shown())

    from_env = resolver.resolve(config=config, environ={**signed, "APP_SERVER__PORT": "9200"})
    checks.equal("env beats the file", 9200, from_env.get("server.port").value)
    checks.equal("env provenance", "env", from_env.get("server.port").source)

    flagged = resolver.resolve(
        config=config,
        environ={**signed, "APP_SERVER__PORT": "9200"},
        flags=["server.port=9300", "log.level=debug"],
    )
    checks.equal("flag beats everything", 9300, flagged.get("server.port").value)
    checks.equal("flag provenance", "flag", flagged.get("server.port").source)
    untouched = flagged.get("features.rate_limit").source
    checks.equal("untouched key stays at its default", "default", untouched)
    checks.equal("duration arrives as milliseconds", 2500, flagged.get("server.timeout").value)

    missing = resolver.resolve(environ={})
    checks.ok("missing required key is a problem", not missing.ok)
    checks.ok(
        "the message names the variable",
        any("APP_AUTH__SIGNING_KEY" in problem for problem in missing.problems),
        str(missing.problems),
    )
    checks.raises(
        "unresolved key is not silently None",
        "did not resolve",
        lambda: missing.get("auth.signing_key"),
    )

    masked = plain.get("auth.signing_key")
    checks.equal("a secret is masked", "***", masked.shown())
    checks.equal("a secret opens on request", "s3cret", masked.shown(True))

    unset = resolver.resolve(environ={"APP_AUTH__SIGNING_KEY": "k"})
    checks.equal(
        "a shipped secret default is visible",
        ["db.url"],
        [value.key.name for value in unset.default_secrets()],
    )
    supplied = resolver.resolve(
        environ={"APP_AUTH__SIGNING_KEY": "k", "APP_DB__URL": "postgres://x"}
    )
    checks.equal(
        "an overridden secret is not",
        [],
        [value.key.name for value in supplied.default_secrets()],
    )

    broken = resolver.resolve(config=FIXTURES / "broken.toml", environ={})
    checks.ok(
        "every problem is reported at once",
        len(broken.problems) >= 4,
        str(broken.problems),
    )
    checks.ok("the good values still resolve", broken.get("db.pool_size").value == 5)


def _cli(checks: Checks) -> None:
    from . import cli

    environ = {"APP_AUTH__SIGNING_KEY": "s3cret", "APP_SERVER__PORT": "9200"}
    saved = dict(resolver.os.environ)
    try:
        resolver.os.environ.clear()
        resolver.os.environ.update(environ)
        checks.equal("check exits 0", 0, cli.main(["check"]))
        checks.equal(
            "strict gates a shipped secret",
            cli.EXIT_DEFAULT_SECRET,
            cli.main(["check", "--strict"]),
        )
        resolver.os.environ["APP_DB__URL"] = "postgres://localhost/app"
        strict = cli.main(["check", "--strict"])
        checks.equal("strict passes once the secret is supplied", 0, strict)
        checks.equal(
            "get refuses a secret",
            cli.EXIT_UNUSABLE,
            cli.main(["get", "db.url"]),
        )
        checks.equal("get --reveal prints it", 0, cli.main(["get", "db.url", "--reveal"]))
        checks.equal(
            "an unknown setting is exit 2",
            cli.EXIT_UNUSABLE,
            cli.main(["get", "server.prot"]),
        )
        checks.equal(
            "a broken file is exit 2",
            cli.EXIT_UNUSABLE,
            cli.main(["check", "--config", str(FIXTURES / "broken.toml")]),
        )
        checks.equal(
            "show --json is parseable",
            10,
            len(json.loads(_capture(cli.main, ["show", "--json"]))["values"]),
        )
    finally:
        resolver.os.environ.clear()
        resolver.os.environ.update(saved)


def _capture(call, argv: list[str]) -> str:
    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        call(argv)
    return buffer.getvalue()


def main() -> int:
    checks = Checks()
    _parsing(checks)
    _layers(checks)
    _resolution(checks)
    _cli(checks)
    total = checks.passed + checks.failed
    print(f"selftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
