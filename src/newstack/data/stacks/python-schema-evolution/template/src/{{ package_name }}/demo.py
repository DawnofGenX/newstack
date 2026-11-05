"""Every breaking claim, with the document that proves it.

A rule that says "a document that passed the old schema fails the new one" is a
claim, and a claim on its own is how schema tools get a reputation for crying
wolf. So each one names a witness: a real document, validated against both
schemas by the same code a user would run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import schema
from .compare import Report, compare

# Which document disproves each breaking rule. Verified, not trusted: a witness
# that validates against the new schema counts as unproven.
WITNESSES = {
    "required-added": "missing-currency.json",
    "enum-value-removed": "retired-type.json",
    "maximum-added": "over-limit.json",
    "additional-properties-closed": "extra-member.json",
}

# Rules about a member disappearing are reader claims: no document can fail,
# because the old documents are still valid. The evidence is the contract.
READER_RULES = frozenset({"property-removed"})


@dataclass(frozen=True)
class Step:
    rule: str
    level: str
    witness: str
    evidence: str

    def line(self) -> str:
        return f"{self.level:<8} {self.rule:<30} {self.witness:<22} {self.evidence}"


@dataclass(frozen=True)
class Proof:
    steps: tuple[Step, ...]
    proven: int
    reader: int
    unproven: int

    @property
    def ok(self) -> bool:
        return self.unproven == 0

    def lines(self) -> list[str]:
        body = [step.line() for step in self.steps]
        body.append(
            f"proof    {self.proven} validator claim(s) shown by a real document, "
            f"{self.reader} reader claim(s), {self.unproven} unproven"
        )
        return body


def fixtures_dir() -> Path:
    """fixtures/ beside the project: a wheel ships the code, not the sample data."""
    for candidate in (Path.cwd() / "fixtures", Path(__file__).resolve().parents[2] / "fixtures"):
        if (candidate / "v1.json").is_file():
            return candidate
    raise schema.SchemaError("cannot find fixtures/v1.json; run this from the project root")


def documents(directory: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        found[path.name] = json.loads(path.read_text())
    return found


def prove(
    report: Report, old: dict[str, Any], new: dict[str, Any], corpus: dict[str, Any]
) -> Proof:
    steps: list[Step] = []
    proven = reader = unproven = 0
    for finding in report.breaking:
        if finding.rule in READER_RULES:
            steps.append(Step(finding.rule, "reader", "(reader)", finding.message))
            reader += 1
            continue
        name = WITNESSES.get(finding.rule)
        if name is None or name not in corpus:
            steps.append(
                Step(finding.rule, "unproven", name or "-", "no witness document is configured")
            )
            unproven += 1
            continue
        document = corpus[name]
        before = schema.validate(old, old, document)
        if before:
            steps.append(
                Step(
                    finding.rule,
                    "unproven",
                    name,
                    f"the witness already fails the old schema: {before[0]}",
                )
            )
            unproven += 1
            continue
        after = schema.validate(new, new, document)
        if not after:
            steps.append(
                Step(
                    finding.rule,
                    "unproven",
                    name,
                    "the witness still validates against the new schema",
                )
            )
            unproven += 1
            continue
        steps.append(Step(finding.rule, "breaking", name, after[0]))
        proven += 1
    steps.sort(key=lambda step: step.rule)
    return Proof(tuple(steps), proven, reader, unproven)


def run(root: Path | None = None) -> tuple[Proof, Report, Report, Report]:
    """Compare v1 with v2 (proved), and report v3 (safe) and v4 (risky)."""
    root = root or fixtures_dir()
    v1 = schema.load(root / "v1.json")
    v2 = schema.load(root / "v2.json")
    v3 = schema.load(root / "v3.json")
    v4 = schema.load(root / "v4.json")
    report = compare(v1, v2)
    proof = prove(report, v1, v2, documents(root / "documents"))
    return proof, report, compare(v1, v3), compare(v1, v4)


def render(proof: Proof, report: Report, additive: Report, undecidable: Report) -> list[str]:
    lines = [
        f"schema evolution: v1 -> v2 is {report.verdict}, "
        f"{len(report.breaking)} breaking change(s) to prove",
        "",
    ]
    lines.extend(proof.lines())
    lines.append("")
    lines.append(
        f"also     v1 -> v3 is {additive.verdict} ({len(additive.breaking)} breaking), "
        f"v1 -> v4 is {undecidable.verdict} ({len(undecidable.risky)} risky)"
    )
    return lines
