"""Adopt an existing project: copy a stack's infrastructure, additively.

The rule that makes this safe: an existing file is never opened for writing. Anything
already present is reported as "kept", and anything that would need a merge inside a
file (a ruff block in someone's pyproject, a test script in their package.json) is
reported as a manual step instead of being attempted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .registry import Stack, load_stacks
from .render import TemplateError, render_tree

# Files adopt must never copy into someone else's project: they carry identity
# (licence, name, entrypoints) rather than infrastructure.
FORBIDDEN = frozenset(
    {
        "README.md",
        "README.rst",
        "LICENSE",
        "LICENSE.md",
        "pyproject.toml",
        "package.json",
        "go.mod",
        "Cargo.toml",
    }
)


@dataclass
class PendingFile:
    rel: str
    payload: bytes
    executable: bool = False


@dataclass
class AdoptionPlan:
    stack: Stack
    root: Path
    detected: bool = True
    add: list[PendingFile] = field(default_factory=list)
    keep: list[str] = field(default_factory=list)
    manual: list[str] = field(default_factory=list)
    tests_available: bool = False

    @property
    def added(self) -> list[str]:
        return [item.rel for item in self.add]

    def as_dict(self) -> dict:
        return {
            "stack": self.stack.name,
            "root": str(self.root),
            "detected": self.detected,
            "added": self.added,
            "kept": self.keep,
            "manual": self.manual,
            "tests_available": self.tests_available,
        }


def detect_stacks(root: Path) -> list[Stack]:
    """Stacks whose markers match *root*; generic fallbacks are dropped on a specific match.

    Inside the fallback group a content-aware marker beats a bare filename: the
    Kotlin CLI wants a ``pom.xml`` that mentions ``kotlin``, and without this rule
    every Kotlin project would also match the generic ``java-maven-cli`` fallback
    and come out ambiguous.
    """
    stacks = load_stacks()
    matched = [stack for stack in stacks.values() if stack.detect and stack.matches(root)]
    specific = [stack for stack in matched if not stack.detect_fallback]
    if specific:
        return specific
    fallbacks = [stack for stack in matched if stack.detect_fallback]
    content_aware = [stack for stack in fallbacks if any(rule.contains for rule in stack.detect)]
    return content_aware or fallbacks


def _manual_steps(stack: Stack, root: Path) -> list[str]:
    steps: list[str] = []
    if stack.language == "python":
        target = root / "pyproject.toml"
        if not target.is_file():
            steps.append("no pyproject.toml found: `newstack new` is a better fit than adopt")
        else:
            steps.append(
                "merge the stack's [tool.ruff] / [tool.pytest.ini_options] blocks into "
                "pyproject.toml by hand (adopt never edits existing files)"
            )
    elif stack.language in {"node", "html"}:
        target = root / "package.json"
        if target.is_file():
            steps.append(
                "add the stack's lint/test scripts to package.json by hand "
                "(adopt never edits existing files)"
            )
    elif stack.language == "go":
        if not (root / ".gitignore").exists():
            steps.append("consider adding bin/ to your .gitignore for build output")
    elif stack.language == "rust":
        steps.append("Cargo.lock should be committed for binaries; .gitignore keeps /target out")
    return steps


def plan_adoption(
    stack: Stack,
    root: Path,
    context: dict,
    *,
    with_tests: bool = False,
    detected: bool = True,
) -> AdoptionPlan:
    """Work out what adopt would do, without touching the filesystem."""
    if not stack.adopt:
        raise TemplateError(f"stack '{stack.name}' declares no adoptable files")

    wanted = list(stack.adopt)
    if with_tests:
        wanted.extend(stack.adopt_tests)

    forbidden = sorted(set(wanted) & FORBIDDEN)
    if forbidden:
        raise TemplateError(
            f"stack '{stack.name}' tries to adopt files that carry project identity: "
            f"{', '.join(forbidden)}"
        )

    entries, _dirs = render_tree(stack.template_dir, context)
    by_path = {rel: (payload, executable) for rel, payload, executable in entries}

    missing = [rel for rel in wanted if rel not in by_path]
    if missing:
        raise TemplateError(
            f"stack '{stack.name}' lists adoptable files that are not in its template: "
            f"{', '.join(missing)}"
        )

    plan = AdoptionPlan(stack=stack, root=root, detected=detected)
    plan.tests_available = bool(stack.adopt_tests) and with_tests
    for rel in wanted:
        if (root / rel).exists():
            plan.keep.append(rel)
            continue
        payload, executable = by_path[rel]
        plan.add.append(PendingFile(rel=rel, payload=payload, executable=executable))

    plan.manual = _manual_steps(stack, root)
    return plan


def apply_plan(plan: AdoptionPlan) -> list[str]:
    """Write the planned files. Only touches paths that did not exist when planned."""
    written: list[str] = []
    for item in plan.add:
        target = plan.root / item.rel
        if target.exists():  # someone else created it since planning: leave it alone
            plan.keep.append(item.rel)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(item.payload)
        if item.executable:
            target.chmod(0o755)
        written.append(item.rel)
    return written
