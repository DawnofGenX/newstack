"""Prove a stack works: generate it into a throwaway directory and run its checks."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .registry import Stack
from .render import generate, render_string


@dataclass
class StepOutcome:
    name: str
    ok: bool
    seconds: float
    skipped: str | None = None
    output: str = ""


@dataclass
class CheckResult:
    stack: str
    title: str
    ok: bool
    seconds: float
    directory: str
    outcomes: list[StepOutcome] = field(default_factory=list)

    @property
    def skipped(self) -> list[str]:
        return [o.name for o in self.outcomes if o.skipped]

    @property
    def failed(self) -> list[StepOutcome]:
        return [o for o in self.outcomes if not o.ok and not o.skipped]

    def as_dict(self) -> dict:
        return {
            "stack": self.stack,
            "title": self.title,
            "ok": self.ok,
            "seconds": round(self.seconds, 2),
            "directory": self.directory,
            "steps": [
                {
                    "name": o.name,
                    "ok": o.ok,
                    "skipped": o.skipped,
                    "seconds": round(o.seconds, 2),
                    "output": o.output,
                }
                for o in self.outcomes
            ],
        }


def missing_tools(stack: Stack) -> list[str]:
    """Toolchains this stack needs that are not on PATH right now."""
    needed = {tool for step in stack.verify for tool in step.tools}
    return sorted(tool for tool in needed if shutil.which(tool) is None)


def _tail(text: str, limit: int = 4000) -> str:
    text = text.strip()
    return text if len(text) <= limit else "…\n" + text[-limit:]


def check_stack(
    stack: Stack,
    context: dict,
    *,
    keep: bool = False,
    verbose: bool = False,
    project_name: str = "check-app",
) -> CheckResult:
    root = Path(tempfile.mkdtemp(prefix=f"newstack-{stack.name}-"))
    started = time.perf_counter()
    result = CheckResult(
        stack=stack.name, title=stack.title, ok=True, seconds=0.0, directory=str(root)
    )
    try:
        generate(stack.template_dir, root, context)
        if not stack.verify:
            result.outcomes.append(StepOutcome(name="generate", ok=True, seconds=0.0))
        for step in stack.verify:
            absent = [tool for tool in step.tools if shutil.which(tool) is None]
            if absent:
                result.outcomes.append(
                    StepOutcome(
                        name=step.name,
                        ok=False,
                        seconds=0.0,
                        skipped=f"missing {', '.join(absent)}",
                    )
                )
                result.ok = False
                continue
            step_started = time.perf_counter()
            try:
                completed = subprocess.run(
                    render_string(step.cmd, context),
                    shell=True,
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=step.timeout,
                )
                ok = completed.returncode == 0
                output = (completed.stdout or "") + (completed.stderr or "")
            except subprocess.TimeoutExpired:
                ok = False
                output = f"timed out after {step.timeout}s"
            result.outcomes.append(
                StepOutcome(
                    name=step.name,
                    ok=ok,
                    seconds=time.perf_counter() - step_started,
                    output=_tail(output) if verbose or not ok else "",
                )
            )
            if not ok:
                result.ok = False
                break
    finally:
        result.seconds = time.perf_counter() - started
        if not keep:
            shutil.rmtree(root, ignore_errors=True)
    return result
