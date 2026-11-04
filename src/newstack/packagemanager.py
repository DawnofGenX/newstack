"""The JavaScript package manager a generated project uses.

A JavaScript stack lists the managers its template has been proven with in
``stack.json``, most preferred first::

    "package_manager": ["npm", "pnpm", "yarn"]

``--package-manager`` picks one of them; the first entry is the default. Every
place the manager appears — the install command, the script runner, the lockfile
name a README tells you to commit, the CI step that prepares it — is rendered
from one set of context keys, so a project cannot end up half npm and half pnpm.

Only the three managers every JavaScript toolchain shares commands with are
modelled. A stack that needs something else should say so in its manifest rather
than grow a fourth dialect here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .registry import RegistryError, Stack

DEFAULT = "npm"


@dataclass(frozen=True)
class Manager:
    """One package manager, described by what a template needs to write."""

    name: str
    #: install dependencies from package.json (no lockfile yet)
    install: str
    #: install from a committed lockfile, exactly as CI should
    ci_install: str
    #: prefix that runs a script defined in package.json
    run: str
    #: run the test script
    test: str
    #: the lockfile this manager leaves behind
    lock: str
    #: CI one-liner that makes the manager available and prints its version
    setup: str
    #: log files the manager writes that belong in .gitignore
    ignore: str
    #: how a README should name the requirement
    prereq: str


MANAGERS = (
    Manager(
        name="npm",
        install="npm install --no-audit --no-fund",
        ci_install="npm ci",
        run="npm run",
        test="npm test",
        lock="package-lock.json",
        setup="npm --version",
        ignore="npm-debug.log*",
        prereq="npm 11",
    ),
    # pnpm is pinned to 10 — what CI installs and what the templates are proven
    # with. pnpm 12 moved build-script approval out of package.json, so a stack
    # that ships `pnpm.onlyBuiltDependencies` must be run on 10 to stay green.
    Manager(
        name="pnpm",
        install="pnpm install",
        ci_install="pnpm install --frozen-lockfile",
        run="pnpm run",
        test="pnpm test",
        lock="pnpm-lock.yaml",
        setup="npm install -g pnpm@10 && pnpm --version",
        ignore="pnpm-debug.log*",
        prereq="pnpm 10",
    ),
    Manager(
        name="yarn",
        install="yarn install",
        ci_install="yarn install --frozen-lockfile",
        run="yarn run",
        test="yarn test",
        lock="yarn.lock",
        setup="npm install -g yarn@1.22.22 && yarn --version",
        ignore="yarn-error.log*",
        prereq="Yarn 1.22 (classic)",
    ),
)

BY_NAME = {manager.name: manager for manager in MANAGERS}
CHOICES = tuple(BY_NAME)


def supported(stack: Stack) -> tuple[str, ...]:
    """Managers this stack's template has been proven with (empty: not a JS stack)."""
    return stack.package_managers


def _chosen(stack: Stack, requested: str | None, recorded: str | None) -> str | None:
    if not stack.package_managers:
        if requested:
            raise RegistryError(f"the {stack.name} stack has no --package-manager choice")
        return None
    if requested and requested not in stack.package_managers:
        raise RegistryError(
            f"the {stack.name} stack supports "
            f"{', '.join(stack.package_managers)} (asked for {requested})"
        )
    if requested:
        return requested
    if recorded in stack.package_managers:
        return recorded
    return stack.package_managers[0]


def context(
    stack: Stack,
    requested: str | None = None,
    *,
    recorded: str | None = None,
) -> dict[str, str]:
    """The ``package_manager*`` render keys for *stack*."""
    name = _chosen(stack, requested, recorded)
    if name is None:
        return {}
    manager = BY_NAME[name]
    return {
        "package_manager": manager.name,
        "package_manager_install": manager.install,
        "package_manager_ci": manager.ci_install,
        "package_manager_run": manager.run,
        "package_manager_test": manager.test,
        "package_manager_lock": manager.lock,
        "package_manager_setup": manager.setup,
        "package_manager_ignore": manager.ignore,
        "package_manager_prereq": manager.prereq,
    }


KEYS = (
    "package_manager",
    "package_manager_install",
    "package_manager_ci",
    "package_manager_run",
    "package_manager_test",
    "package_manager_lock",
    "package_manager_setup",
    "package_manager_ignore",
    "package_manager_prereq",
)


def apply(stack: Stack, context_dict: dict, requested: str | None = None) -> dict:
    """Merge the keys into *context_dict*; raises when the request cannot be honoured."""
    keys = context(stack, requested, recorded=context_dict.get("package_manager"))
    if not keys:
        for key in KEYS:
            context_dict.pop(key, None)
        return context_dict
    context_dict.update(keys)
    return context_dict
