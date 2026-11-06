"""The matcher: the last matching rule wins, and a parent cannot be undone."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .pattern import PatternError, Rule, parse_rules


class PathError(ValueError):
    """A path that cannot be matched as written."""


@dataclass(frozen=True)
class Verdict:
    path: str
    is_dir: bool
    ignored: bool
    rule: Rule | None
    reason: str
    parent: str | None = None

    def lines(self) -> list[str]:
        kind = "directory" if self.is_dir else "file"
        lines = [f"path       {self.path}", f"kind       {kind}"]
        lines.append(f"verdict    {'ignored' if self.ignored else 'not ignored'}")
        if self.rule is not None:
            lines.append(f"rule       line {self.rule.line}: {self.rule.render()}")
        lines.append(f"reason     {self.reason}")
        return lines


def _normalise(path: str) -> str:
    cleaned = path.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    cleaned = cleaned.strip("/")
    if not cleaned:
        raise PathError("an empty path has no name to match")
    parts = cleaned.split("/")
    if any(part in ("", ".") for part in parts):
        raise PathError(f"{path!r} has an empty segment; a path is segments joined by /")
    if any(part == ".." for part in parts):
        raise PathError(f"{path!r} steps outside the tree; a matcher cannot follow ..")
    return cleaned


class Matcher:
    def __init__(self, rules: list[Rule]) -> None:
        if not rules:
            raise PatternError("a matcher without rules can only say nothing")
        self.rules = tuple(rules)

    @classmethod
    def from_lines(cls, lines: list[str]) -> tuple[Matcher, list[Rule]]:
        rules = parse_rules(lines)
        return cls(rules), rules

    @classmethod
    def from_file(cls, path: Path) -> tuple[Matcher, list[Rule]]:
        if not path.exists():
            raise PatternError(f"no such ignore file: {path}")
        return cls.from_lines(path.read_text(encoding="utf-8").splitlines())

    def _last_rule(self, path: str, *, is_dir: bool) -> Rule | None:
        found: Rule | None = None
        for rule in self.rules:
            if rule.matches(path, is_dir=is_dir):
                found = rule
        return found

    def decide(self, path: str, *, is_dir: bool = False) -> Verdict:
        cleaned = _normalise(path)
        parts = cleaned.split("/")
        for depth in range(1, len(parts)):
            parent = "/".join(parts[:depth])
            rule = self._last_rule(parent, is_dir=True)
            if rule is not None and not rule.negated:
                return Verdict(
                    path=cleaned,
                    is_dir=is_dir,
                    ignored=True,
                    rule=rule,
                    reason=(
                        f"its parent {parent!r} is ignored by line {rule.line}, and a "
                        "file cannot be re-included while its parent is excluded"
                    ),
                    parent=parent,
                )
        rule = self._last_rule(cleaned, is_dir=is_dir)
        if rule is None:
            return Verdict(
                path=cleaned,
                is_dir=is_dir,
                ignored=False,
                rule=None,
                reason="no rule matched, so there is nothing to ignore",
            )
        if rule.negated:
            return Verdict(
                path=cleaned,
                is_dir=is_dir,
                ignored=False,
                rule=rule,
                reason=f"line {rule.line} is a negation and it is the last rule that matches",
            )
        return Verdict(
            path=cleaned,
            is_dir=is_dir,
            ignored=True,
            rule=rule,
            reason=f"line {rule.line} is the last rule that matches, and it ignores",
        )

    def ignored(self, path: str, *, is_dir: bool = False) -> bool:
        return self.decide(path, is_dir=is_dir).ignored

    def walk(self, root: Path) -> list[Verdict]:
        if not root.is_dir():
            raise PathError(f"not a directory: {root}")
        verdicts: list[Verdict] = []
        for child in sorted(root.rglob("*")):
            if ".git" in child.parts:
                continue
            relative = child.relative_to(root).as_posix()
            verdicts.append(self.decide(relative, is_dir=child.is_dir()))
        return verdicts
