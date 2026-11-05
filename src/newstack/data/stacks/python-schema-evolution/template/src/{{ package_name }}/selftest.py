"""Checks that need no pytest: every rule, both directions, on real fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from . import demo, schema
from .compare import BREAKING, RISKY, SAFE, compare


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, description: str, condition: bool) -> None:
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            print(f"FAIL  {description}")

    def equal(self, description: str, want: Any, got: Any) -> None:
        self.ok(f"{description}: want {want!r}, got {got!r}", want == got)

    def raises(self, description: str, function: Any, *args: Any, **kwargs: Any) -> None:
        try:
            function(*args, **kwargs)
        except (schema.SchemaError, ValueError):
            self.passed += 1
        except Exception as error:
            self.failed += 1
            print(f"FAIL  {description}: raised {type(error).__name__}, not a SchemaError")
        else:
            self.failed += 1
            print(f"FAIL  {description}: nothing was raised")


def _fixtures() -> Path:
    return demo.fixtures_dir()


def _document(**overrides: Any) -> dict[str, Any]:
    document: dict[str, Any] = {
        "$schema": schema.INPUT_VERSION,
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    document.update(overrides)
    return document


def _types_checks(checks: Checks) -> None:
    narrowed = compare({"type": ["string", "integer"]}, {"type": "string"})
    checks.equal(
        "a dropped type is breaking", [BREAKING], [finding.level for finding in narrowed.findings]
    )
    widened = compare({"type": "string"}, {"type": ["string", "integer"]})
    checks.equal("an added type is safe", [SAFE], [finding.level for finding in widened.findings])
    unbounded = compare({}, {"type": "string"})
    checks.equal(
        "constraining an untyped schema is breaking",
        [BREAKING],
        [finding.level for finding in unbounded.findings],
    )
    freed = compare({"type": "string"}, {})
    checks.equal("removing the type is safe", [SAFE], [finding.level for finding in freed.findings])


def _enum_checks(checks: Checks) -> None:
    removed = compare({"enum": ["a", "b"]}, {"enum": ["a"]})
    checks.equal(
        "a removed enum value is breaking",
        ["enum-value-removed"],
        [f.rule for f in removed.findings],
    )
    added = compare({"enum": ["a"]}, {"enum": ["a", "b"]})
    checks.equal("an added enum value is safe", [SAFE], [f.level for f in added.findings])
    closed = compare({}, {"enum": ["a"]})
    checks.equal(
        "closing an open value set is breaking", [BREAKING], [f.level for f in closed.findings]
    )
    opened = compare({"enum": ["a"]}, {})
    checks.equal("opening a closed set is safe", [SAFE], [f.level for f in opened.findings])


def _bounds_checks(checks: Checks) -> None:
    checks.equal(
        "raising a minimum is breaking",
        ["minimum-increased"],
        [f.rule for f in compare({"minimum": 1}, {"minimum": 5}).findings],
    )
    checks.equal(
        "lowering a minimum is safe",
        [SAFE],
        [f.level for f in compare({"minimum": 5}, {"minimum": 1}).findings],
    )
    checks.equal(
        "lowering a maximum is breaking",
        ["maximum-decreased"],
        [f.rule for f in compare({"maximum": 9}, {"maximum": 5}).findings],
    )
    checks.equal(
        "raising a maximum is safe",
        [SAFE],
        [f.level for f in compare({"maximum": 5}, {"maximum": 9}).findings],
    )
    checks.equal(
        "adding a maximum is breaking",
        ["maximum-added"],
        [f.rule for f in compare({}, {"maximum": 9}).findings],
    )
    checks.equal(
        "a longer allowed string is safe",
        [SAFE],
        [f.level for f in compare({"maxLength": 4}, {"maxLength": 8}).findings],
    )
    checks.equal(
        "a shorter allowed string is breaking",
        ["maxLength-decreased"],
        [f.rule for f in compare({"maxLength": 8}, {"maxLength": 4}).findings],
    )
    checks.equal(
        "a higher minLength is breaking",
        ["minLength-increased"],
        [f.rule for f in compare({"minLength": 1}, {"minLength": 3}).findings],
    )


def _object_checks(checks: Checks) -> None:
    required = compare({"required": ["a"]}, {"required": ["a", "b"]})
    checks.equal(
        "a new required member is breaking", ["required-added"], [f.rule for f in required.findings]
    )
    relaxed = compare({"required": ["a", "b"]}, {"required": ["a"]})
    checks.equal("a dropped requirement is safe", [SAFE], [f.level for f in relaxed.findings])
    removed = compare({"properties": {"a": {}, "b": {}}}, {"properties": {"a": {}}})
    checks.equal(
        "a removed property is breaking", ["property-removed"], [f.rule for f in removed.findings]
    )
    checks.ok(
        "the removed property finding talks about a reader",
        "reader" in removed.findings[0].message,
    )
    closed = compare({"additionalProperties": True}, {"additionalProperties": False})
    checks.equal(
        "closing additionalProperties is breaking",
        ["additional-properties-closed"],
        [f.rule for f in closed.findings],
    )
    opened = compare({"additionalProperties": False}, {"additionalProperties": True})
    checks.equal("opening additionalProperties is safe", [SAFE], [f.level for f in opened.findings])
    nested = compare(
        {"properties": {"a": {"type": "string"}}},
        {"properties": {"a": {"type": "integer"}}},
    )
    checks.equal("a nested change is located", ["$.a"], [f.path for f in nested.findings])
    checks.equal("a nested change is classified", [BREAKING], [f.level for f in nested.findings])


def _misc_checks(checks: Checks) -> None:
    pattern = compare({"pattern": "^a"}, {"pattern": "^b"})
    checks.equal("a changed pattern is risky", [RISKY], [f.level for f in pattern.findings])
    checks.equal(
        "a changed pattern is named", ["pattern-changed"], [f.rule for f in pattern.findings]
    )
    added = compare({}, {"pattern": "^a"})
    checks.equal("an added pattern is risky", [RISKY], [f.level for f in added.findings])
    dropped = compare({"pattern": "^a"}, {})
    checks.equal("a dropped pattern is safe", [SAFE], [f.level for f in dropped.findings])
    const = compare({"const": "a"}, {"const": "b"})
    checks.equal("a changed const is breaking", [BREAKING], [f.level for f in const.findings])
    default = compare({}, {"default": "a"})
    checks.equal("a new default is risky", ["default-added"], [f.rule for f in default.findings])
    deprecated = compare({}, {"deprecated": True})
    checks.equal("a deprecation is risky", ["deprecated"], [f.rule for f in deprecated.findings])
    described = compare({"description": "old"}, {"description": "new"})
    checks.equal("documentation-only changes are ignored", 0, len(described.findings))


def _report_checks(checks: Checks) -> None:
    report = compare({"type": "string"}, {"type": "integer"})
    checks.equal("a breaking report has the breaking verdict", BREAKING, report.verdict)
    checks.ok("a breaking report fails", report.fails())
    risky = compare({}, {"default": "a"})
    checks.ok("a risky report passes without --strict", not risky.fails())
    checks.ok("a risky report fails with --strict", risky.fails(strict=True))
    same = compare({"type": "string"}, {"type": "string"})
    checks.equal("an identical schema is compatible", "compatible", same.verdict)
    checks.equal("an identical schema says so", 1, len(same.lines()))
    payload = report.as_dict()
    checks.equal("the payload names the verdict", BREAKING, payload["verdict"])
    checks.equal("the payload counts the findings", 1, payload["counts"][BREAKING])


def _schema_checks(checks: Checks) -> None:
    v1 = schema.load(_fixtures() / "v1.json")
    v2 = schema.load(_fixtures() / "v2.json")
    documents = demo.documents(_fixtures() / "documents")
    checks.equal(
        "a valid document has no problems", [], schema.validate(v1, v1, documents["with-note.json"])
    )
    problems = schema.validate(v2, v2, documents["missing-currency.json"])
    checks.equal(
        "a missing required member is named", "$: missing required member 'currency'", problems[0]
    )
    problems = schema.validate(v2, v2, documents["extra-member.json"])
    checks.ok(
        "an unexpected member is refused when the schema is closed",
        "unexpected member" in problems[-1],
    )
    checks.ok("an integer satisfies a number type", schema.matches_type(3, "number"))
    checks.ok("a boolean is not an integer", not schema.matches_type(True, "integer"))
    checks.equal("an untyped schema allows any type", None, schema.types_of({}))
    with tempfile.TemporaryDirectory() as folder:
        sample = Path(folder) / "sample.json"
        sample.write_text('{"id": 1}')
        try:
            schema.load(sample)
        except schema.SchemaError as error:
            checks.ok("a document without $schema is refused", "has no $schema" in str(error))
        else:
            checks.failed += 1
            print("FAIL  a document without $schema was accepted")
        missing = Path(folder) / "missing.json"
        try:
            schema.load(missing)
        except schema.SchemaError as error:
            checks.ok("a missing file is named", "cannot read" in str(error))
        else:
            checks.failed += 1
            print("FAIL  a missing file was accepted")


def _fixture_checks(checks: Checks) -> None:
    v1 = schema.load(_fixtures() / "v1.json")
    v2 = schema.load(_fixtures() / "v2.json")
    v3 = schema.load(_fixtures() / "v3.json")
    v4 = schema.load(_fixtures() / "v4.json")
    breaking = compare(v1, v2)
    checks.equal("v1 -> v2 is breaking", BREAKING, breaking.verdict)
    checks.equal("v1 -> v2 has five breaking findings", 5, len(breaking.breaking))
    checks.equal(
        "v1 -> v2 proves each breaking rule",
        [
            "additional-properties-closed",
            "enum-value-removed",
            "maximum-added",
            "property-removed",
            "required-added",
        ],
        sorted(finding.rule for finding in breaking.breaking),
    )
    checks.equal("v1 -> v3 is compatible", "compatible", compare(v1, v3).verdict)
    checks.equal("v1 -> v4 is risky", RISKY, compare(v1, v4).verdict)


def _demo_checks(checks: Checks) -> None:
    proof, report, additive, undecidable = demo.run()
    checks.ok("the demo proves every claim", proof.ok)
    checks.equal("four claims are proven by a document", 4, proof.proven)
    checks.equal("one claim is a reader claim", 1, proof.reader)
    checks.equal("nothing is unproven", 0, proof.unproven)
    checks.equal("every breaking finding has a step", len(report.breaking), len(proof.steps))
    checks.ok(
        "each proven step quotes a real problem",
        all(": " in step.evidence for step in proof.steps if step.level == "breaking"),
    )
    checks.equal("the additive comparison has no breaking findings", 0, len(additive.breaking))
    checks.equal("the undecidable comparison has risky findings", 4, len(undecidable.risky))
    lines = demo.render(proof, report, additive, undecidable)
    checks.ok("the render names the verdict", any("breaking" in line for line in lines))
    checks.ok(
        "the render ends with the proof tally", any(line.startswith("proof ") for line in lines)
    )


def run() -> int:
    checks = Checks()
    groups = (
        ("types", _types_checks),
        ("enums", _enum_checks),
        ("bounds", _bounds_checks),
        ("objects", _object_checks),
        ("misc", _misc_checks),
        ("report", _report_checks),
        ("schema", _schema_checks),
        ("fixtures", _fixture_checks),
        ("demo", _demo_checks),
    )
    for label, group in groups:
        before = checks.failed
        group(checks)
        if checks.failed == before:
            print(f"ok    {label}")
    total = checks.passed + checks.failed
    print(f"selftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
