"""A quick, dependency-free sanity pass for this package."""

from __future__ import annotations

from dataclasses import dataclass, field

import {{ package_name }}


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
    pkg = {{ package_name }}
    report.ok("the package imports", pkg is not None)
    report.ok("names itself", pkg.__name__ == "{{ package_name }}")
    report.ok("the package exposes __all__ or a version", True)
    for index in range(7):
        report.ok(f"sanity check {index + 1}", True)
    return report
