from pathlib import Path

from {{ package_name }} import compare as compare_mod
from {{ package_name }} import demo as subject

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def corpus() -> dict:
    return subject.documents(FIXTURES / "documents")


def test_every_breaking_finding_is_proven_or_spoken_for(v1: dict, v2: dict) -> None:
    report = subject.compare(v1, v2)
    proof = subject.prove(report, v1, v2, corpus())
    assert proof.ok
    assert (proof.proven, proof.reader, proof.unproven) == (4, 1, 0)
    assert len(proof.steps) == len(report.breaking)


def test_each_proof_quotes_the_problem_the_new_schema_reports(v1: dict, v2: dict) -> None:
    report = subject.compare(v1, v2)
    proof = subject.prove(report, v1, v2, corpus())
    by_rule = {step.rule: step for step in proof.steps}
    assert by_rule["required-added"].evidence == "$: missing required member 'currency'"
    assert (
        by_rule["enum-value-removed"].evidence
        == "$.type: 'order.paid' is not one of ['order.created']"
    )
    assert by_rule["maximum-added"].evidence == "$.amount: above the maximum 1000000"
    assert by_rule["additional-properties-closed"].evidence == "$.meta: unexpected member 'meta'"


def test_the_reader_claim_names_the_member_that_disappeared(v1: dict, v2: dict) -> None:
    report = subject.compare(v1, v2)
    proof = subject.prove(report, v1, v2, corpus())
    step = next(step for step in proof.steps if step.rule == "property-removed")
    assert step.level == "reader"
    assert step.witness == "(reader)"


def test_an_additive_change_has_nothing_to_prove(v1: dict, v3: dict) -> None:
    """v3 is additive, so every witness validates: the claim must not be 'proven'."""
    report = subject.compare(v1, v3)
    proof = subject.prove(report, v1, v3, corpus())
    assert proof.proven == 0
    assert proof.unproven == 0
    assert proof.steps == ()


def test_a_witness_that_fails_the_old_schema_is_not_evidence(v1: dict, v2: dict) -> None:
    broken = dict(corpus())
    broken["missing-currency.json"] = {"id": "ord_9", "amount": "free"}
    report = subject.compare(v1, v2)
    proof = subject.prove(report, v1, v2, broken)
    step = next(step for step in proof.steps if step.rule == "required-added")
    assert step.level == "unproven"
    assert "already fails the old schema" in step.evidence
    assert not proof.ok


def test_a_missing_witness_is_named_as_unproven(v1: dict, v2: dict) -> None:
    report = subject.compare(v1, v2)
    proof = subject.prove(report, v1, v2, {})
    step = next(step for step in proof.steps if step.rule == "maximum-added")
    assert step.level == "unproven"
    assert step.evidence == "no witness document is configured"


def test_a_rule_without_a_witness_entry_cannot_be_proven() -> None:
    report = subject.compare({"properties": {"a": {}, "b": {}}}, {"properties": {"a": {}}})
    report.findings.append(
        compare_mod.Finding(
            path="$.c", rule="invented-rule", level=compare_mod.BREAKING, message="x"
        )
    )
    proof = subject.prove(report, {}, {}, {})
    assert proof.unproven == 1
    assert not proof.ok


def test_the_run_reports_three_comparisons() -> None:
    proof, report, additive, undecidable = subject.run(FIXTURES)
    assert proof.ok
    assert report.verdict == compare_mod.BREAKING
    assert additive.breaking == []
    assert undecidable.verdict == compare_mod.RISKY


def test_the_rendered_demo_reads_like_a_report(v1: dict, v2: dict, v3: dict, v4: dict) -> None:
    report = subject.compare(v1, v2)
    proof = subject.prove(report, v1, v2, corpus())
    lines = subject.render(proof, report, subject.compare(v1, v3), subject.compare(v1, v4))
    assert lines[0] == "schema evolution: v1 -> v2 is breaking, 5 breaking change(s) to prove"
    assert lines[-1] == "also     v1 -> v3 is compatible (0 breaking), v1 -> v4 is risky (4 risky)"
    assert any(line.startswith("proof    4 validator claim(s)") for line in lines)


def test_a_document_dir_is_read_in_sorted_order() -> None:
    names = list(subject.documents(FIXTURES / "documents"))
    assert names == sorted(names)
    assert "missing-currency.json" in names


def test_the_proof_is_deterministic(v1: dict, v2: dict) -> None:
    report = subject.compare(v1, v2)
    first = subject.prove(report, v1, v2, corpus())
    second = subject.prove(report, v1, v2, corpus())
    assert first == second
