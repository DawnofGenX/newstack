"""The rules, one function each, and a report that says which of them fired.

The question this answers is deliberately narrow: can a document that validated
against the old schema fail against the new one, or can a field a reader relied
on disappear? Anything that does neither is reported as safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import deref, types_of

BREAKING = "breaking"
RISKY = "risky"
SAFE = "safe"

# Keys that change documentation, not the contract.
IGNORED = frozenset({"$schema", "$id", "$comment", "title", "description", "examples", "example"})


def _names(types: set[str]) -> str:
    return "/".join(sorted(types))


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    level: str
    message: str

    def line(self) -> str:
        return f"{self.level:<8} {self.rule:<26} {self.path}  {self.message}"

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "rule": self.rule, "level": self.level, "message": self.message}


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def of(self, level: str) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == level]

    @property
    def breaking(self) -> list[Finding]:
        return self.of(BREAKING)

    @property
    def risky(self) -> list[Finding]:
        return self.of(RISKY)

    @property
    def safe(self) -> list[Finding]:
        return self.of(SAFE)

    @property
    def verdict(self) -> str:
        if self.breaking:
            return BREAKING
        if self.risky:
            return RISKY
        return "compatible"

    def fails(self, strict: bool = False) -> bool:
        return bool(self.breaking) or (strict and bool(self.risky))

    def lines(self) -> list[str]:
        if not self.findings:
            return ["no change that affects a document or a reader"]
        body = [finding.line() for finding in self.findings]
        body.append(
            f"{len(self.breaking)} breaking, {len(self.risky)} risky, {len(self.safe)} safe "
            f"-> {self.verdict}"
        )
        return body

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "findings": [finding.as_dict() for finding in self.findings],
            "counts": {
                BREAKING: len(self.breaking),
                RISKY: len(self.risky),
                SAFE: len(self.safe),
            },
        }


class Comparison:
    def __init__(self, old: dict[str, Any], new: dict[str, Any]) -> None:
        self.old = old
        self.new = new
        self.report = Report()

    def add(self, path: str, rule: str, level: str, message: str) -> None:
        self.report.findings.append(Finding(path=path, rule=rule, level=level, message=message))

    def walk(self, path: str = "$") -> Report:
        self._compare(self.old, self.new, path)
        self.report.findings.sort(key=lambda finding: (finding.path, finding.rule))
        return self.report

    def _compare(self, old: dict[str, Any], new: dict[str, Any], path: str) -> None:
        old = deref(self.old, old)
        new = deref(self.new, new)
        self._types(old, new, path)
        self._enum(old, new, path)
        self._bounds(old, new, path)
        self._object(old, new, path)
        self._misc(old, new, path)

    def _types(self, old: dict[str, Any], new: dict[str, Any], path: str) -> None:
        before, after = types_of(old), types_of(new)
        if before is None and after is None:
            return
        if before is None:
            names = "/".join(sorted(after or []))
            self.add(path, "type-narrowed", BREAKING, f"was any type, now {names}")
            return
        if after is None:
            self.add(path, "type-widened", SAFE, "the type constraint was removed")
            return
        gone, added = before - after, after - before
        if gone and added:
            self.add(path, "type-changed", BREAKING, f"{_names(before)} -> {_names(after)}")
            return
        if gone:
            self.add(path, "type-narrowed", BREAKING, f"{_names(gone)} no longer accepted")
        if added:
            self.add(path, "type-widened", SAFE, f"{_names(added)} now accepted as well")

    def _enum(self, old: dict[str, Any], new: dict[str, Any], path: str) -> None:
        before = old.get("enum")
        after = new.get("enum")
        if before is None and after is None:
            return
        if before is None:
            self.add(path, "enum-added", BREAKING, "a closed set of values replaced an open one")
            return
        if after is None:
            self.add(path, "enum-removed", SAFE, "the closed set of values was opened up")
            return
        for value in before:
            if value not in after:
                self.add(
                    path,
                    "enum-value-removed",
                    BREAKING,
                    f"{value!r} is no longer allowed",
                )
        for value in after:
            if value not in before:
                self.add(path, "enum-value-added", SAFE, f"{value!r} is new")

    def _bounds(self, old: dict[str, Any], new: dict[str, Any], path: str) -> None:
        for name, worse, word in (
            ("minimum", "increased", "narrower"),
            ("maximum", "decreased", "narrower"),
        ):
            before, after = old.get(name), new.get(name)
            if before == after:
                continue
            if before is None and after is not None:
                self.add(path, f"{name}-added", BREAKING, f"{name} {after} now bounds documents")
            elif after is None:
                self.add(path, f"{name}-removed", SAFE, f"{name} {before} was dropped")
            elif (after > before) == (worse == "increased"):
                self.add(
                    path,
                    f"{name}-{worse}",
                    BREAKING,
                    f"{name} moved {before} -> {after}, which is {word}",
                )
            else:
                self.add(path, f"{name}-relaxed", SAFE, f"{name} moved {before} -> {after}")
        for name, breaking in (
            ("minLength", "minLength-increased"),
            ("maxLength", "maxLength-decreased"),
        ):
            before, after = old.get(name), new.get(name)
            if before == after:
                continue
            if before is None and after is not None:
                self.add(path, f"{name}-added", BREAKING, f"{name} {after} now bounds strings")
            elif after is None:
                self.add(path, f"{name}-removed", SAFE, f"{name} {before} was dropped")
            elif (after > before) == (name == "minLength"):
                self.add(path, breaking, BREAKING, f"{name} moved {before} -> {after}")
            else:
                self.add(path, f"{name}-relaxed", SAFE, f"{name} moved {before} -> {after}")

    def _object(self, old: dict[str, Any], new: dict[str, Any], path: str) -> None:
        before_required = set(old.get("required", []))
        after_required = set(new.get("required", []))
        for name in sorted(after_required - before_required):
            self.add(
                path,
                "required-added",
                BREAKING,
                f"{name!r} is required now; documents written against the old schema omit it",
            )
        for name in sorted(before_required - after_required):
            self.add(path, "required-relaxed", SAFE, f"{name!r} is optional now")

        before_props = old.get("properties", {}) or {}
        after_props = new.get("properties", {}) or {}
        for name in sorted(before_props):
            child = f"{path}.{name}"
            if name not in after_props:
                self.add(
                    child,
                    "property-removed",
                    BREAKING,
                    "the member is gone from the contract; a reader that uses it gets nothing",
                )
        for name in sorted(after_props):
            if name not in before_props:
                child = f"{path}.{name}"
                self.add(child, "property-added", SAFE, "a new optional member")
        for name in sorted(set(before_props) & set(after_props)):
            self._compare(before_props[name], after_props[name], f"{path}.{name}")

        before_extra, after_extra = (
            old.get("additionalProperties", True),
            new.get("additionalProperties", True),
        )
        if before_extra is not False and after_extra is False:
            self.add(
                path,
                "additional-properties-closed",
                BREAKING,
                "documents carrying undeclared members are now invalid",
            )
        elif before_extra is False and after_extra is not False:
            self.add(path, "additional-properties-opened", SAFE, "undeclared members are allowed")

    def _misc(self, old: dict[str, Any], new: dict[str, Any], path: str) -> None:
        if ("const" in old or "const" in new) and old.get("const") != new.get("const"):
            self.add(
                path,
                "const-changed",
                BREAKING,
                f"{old.get('const')!r} -> {new.get('const')!r}",
            )
        if old.get("pattern") != new.get("pattern"):
            if "pattern" in old and "pattern" in new:
                self.add(path, "pattern-changed", RISKY, "a changed pattern can reject old values")
            elif "pattern" in new:
                self.add(path, "pattern-added", RISKY, "a new pattern can reject old values")
            elif "pattern" in old:
                self.add(path, "pattern-removed", SAFE, "the pattern constraint was dropped")
        if old.get("format") != new.get("format"):
            before_format = old.get("format") or "none"
            after_format = new.get("format") or "none"
            self.add(path, "format-changed", RISKY, f"{before_format} -> {after_format}")
        if "default" in new and old.get("default") != new.get("default"):
            rule = "default-changed" if "default" in old else "default-added"
            self.add(path, rule, RISKY, "a default changes what a reader sees without a value")
        if new.get("deprecated") and not old.get("deprecated"):
            self.add(path, "deprecated", RISKY, "the member is marked deprecated")


def compare(old: dict[str, Any], new: dict[str, Any]) -> Report:
    return Comparison(old, new).walk()
