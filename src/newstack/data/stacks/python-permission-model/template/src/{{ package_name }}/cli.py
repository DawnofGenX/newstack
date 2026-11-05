"""permctl: decide, audit, demonstrate. Nothing is written and nothing is stored."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import patterns
from .engine import Request, decide
from .policy import Policy, PolicyError, load

PROGRAM = "{{ npm_name }}"
EXIT_ALLOW = 0
EXIT_DENY = 1
EXIT_UNUSABLE = 2

USAGE = """\
usage: permctl decide --policy FILE --subject NAME --action ACTION --resource PATH
                      [--subject-attr KEY=VALUE]... [--resource-attr KEY=VALUE]... [--json]
       permctl check --policy FILE
       permctl demo
       permctl selftest
       permctl --version
"""


class UsageError(ValueError):
    pass


def _pairs(values: list[str], flag: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for value in values:
        key, separator, item = value.partition("=")
        if not separator or not key:
            raise UsageError(f"{flag} needs KEY=VALUE, got {value!r}")
        attributes[key] = item
    return attributes


def _take(argv: list[str], flag: str) -> str | None:
    try:
        at = argv.index(flag)
    except ValueError:
        return None
    if at + 1 >= len(argv):
        raise UsageError(f"{flag} needs a value")
    value = argv[at + 1]
    del argv[at : at + 2]
    return value


def _take_all(argv: list[str], flag: str) -> list[str]:
    values: list[str] = []
    while flag in argv:
        at = argv.index(flag)
        if at + 1 >= len(argv):
            raise UsageError(f"{flag} needs a value")
        values.append(argv[at + 1])
        del argv[at : at + 2]
    return values


def _require(value: str | None, flag: str) -> str:
    if value is None:
        raise UsageError(f"{flag} is required")
    return value


def _policy(argv: list[str]) -> Policy:
    path = _require(_take(argv, "--policy"), "--policy")
    return load(Path(path))


def command_decide(argv: list[str]) -> int:
    as_json = "--json" in argv
    if as_json:
        argv.remove("--json")
    subject = _require(_take(argv, "--subject"), "--subject")
    action = _require(_take(argv, "--action"), "--action")
    resource = _require(_take(argv, "--resource"), "--resource")
    subject_attributes = _pairs(_take_all(argv, "--subject-attr"), "--subject-attr")
    resource_attributes = _pairs(_take_all(argv, "--resource-attr"), "--resource-attr")
    policy = _policy(argv)
    if argv:
        raise UsageError(f"unexpected argument(s): {' '.join(argv)}")
    decision = decide(
        policy, Request(subject, action, resource, subject_attributes, resource_attributes)
    )
    if as_json:
        print(json.dumps(decision.as_dict(), indent=2))
    else:
        for line in decision.lines():
            print(line)
    return EXIT_ALLOW if decision.allowed else EXIT_DENY


def findings(policy: Policy) -> list[str]:
    """Rules that cannot do what they look like they do."""
    found: list[str] = []
    reachable: set[str] = set()
    for assignment in policy.assignments:
        reachable.update(policy.chain(assignment.role))
    for name in sorted(policy.roles):
        if name not in reachable:
            found.append(
                f"role {name} is declared but never assigned, so every rule using it is dead"
            )
    denies = [rule for rule in policy.rules if rule.effect == "deny" and not rule.condition]
    for allow in policy.rules:
        if allow.effect != "allow":
            continue
        for deny in denies:
            covers_roles = (not deny.roles and "*" in deny.subjects) or set(deny.roles) <= set(
                allow.roles
            )
            if (
                deny.action == allow.action
                and deny.resource == allow.resource
                and covers_roles
                and deny.subjects
            ):
                found.append(
                    f"allow {allow.id} can never win: deny {deny.id} covers the same "
                    "action and resource"
                )
    for rule in policy.rules:
        last = patterns.segments(rule.resource)[-1]
        if not last.endswith("*") or last.endswith("**"):
            continue
        prefix = rule.resource[: -len("*")]
        depth = len(patterns.segments(rule.resource))
        if any(
            other.resource.startswith(prefix) and len(patterns.segments(other.resource)) > depth
            for other in policy.rules
        ):
            found.append(
                f"rule {rule.id}: {rule.resource} matches one segment only, and other "
                f"rules reach deeper under {prefix}; write {prefix}** if you meant a subtree"
            )
    return found


def command_check(argv: list[str]) -> int:
    policy = _policy(argv)
    if argv:
        raise UsageError(f"unexpected argument(s): {' '.join(argv)}")
    found = findings(policy)
    print(
        f"policy    {len(policy.roles)} roles, {len(policy.assignments)} assignments, "
        f"{len(policy.rules)} rules"
    )
    for name in sorted(policy.roles):
        print(f"role      {name}: inherits {', '.join(policy.roles[name].inherits) or 'nothing'}")
    if not found:
        print("result    no findings")
        return EXIT_ALLOW
    for item in found:
        print(f"finding   {item}")
    print(f"result    {len(found)} finding(s)")
    return EXIT_DENY


def command_demo(argv: list[str]) -> int:
    if argv:
        raise UsageError("demo takes no arguments")
    from .demo import main as demo_main

    return demo_main()


def command_selftest(argv: list[str]) -> int:
    if argv:
        raise UsageError("selftest takes no arguments")
    from .selftest import main as selftest_main

    return selftest_main()


COMMANDS = {
    "decide": command_decide,
    "check": command_check,
    "demo": command_demo,
    "selftest": command_selftest,
}


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in ("-h", "--help", "help"):
        print(USAGE, end="")
        return EXIT_ALLOW if arguments else EXIT_UNUSABLE
    if arguments[0] in ("-V", "--version"):
        print(f"{PROGRAM} 0.4.0")
        return EXIT_ALLOW
    command = arguments.pop(0)
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"{PROGRAM}: error: unknown command {command!r}", file=sys.stderr)
        print(USAGE, end="", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        return handler(arguments)
    except UsageError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except PolicyError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except (patterns.PatternError, ValueError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
