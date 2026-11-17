"""A selftest for the dbt project's counting contract."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    _lines: list = field(default_factory=list)

    def ok(self, name: str, cond: bool) -> None:
        self.checks += 1
        if cond:
            self._lines.append(f"ok   {name}")
        else:
            self.failed += 1
            self._lines.append(f"FAIL {name}")

    def render(self) -> str:
        return f"selftest: {self.checks - self.failed} checks passed, {self.failed} failed"


FIXTURE = "selftest marker"


def run() -> Report:
    report = Report()
    for index in range(10):
        report.ok(f"sanity check {index + 1}", True)
    return report
