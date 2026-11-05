from {{ package_name }} import compare as subject


def rules(report: subject.Report) -> list[str]:
    return [finding.rule for finding in report.findings]


def levels(report: subject.Report) -> list[str]:
    return [finding.level for finding in report.findings]


def test_replacing_the_type_is_one_breaking_finding_not_two() -> None:
    report = subject.compare({"type": "string"}, {"type": "integer"})
    assert rules(report) == ["type-changed"]
    assert report.findings[0].message == "string -> integer"


def test_a_dropped_type_breaks_writers() -> None:
    report = subject.compare({"type": ["string", "integer"]}, {"type": "string"})
    assert rules(report) == ["type-narrowed"]
    assert levels(report) == [subject.BREAKING]
    assert "integer no longer accepted" in report.findings[0].message


def test_an_added_type_is_safe_for_writers() -> None:
    report = subject.compare({"type": "string"}, {"type": ["string", "integer"]})
    assert rules(report) == ["type-widened"]
    assert levels(report) == [subject.SAFE]


def test_constraining_an_untyped_schema_is_breaking() -> None:
    report = subject.compare({}, {"type": "string"})
    assert rules(report) == ["type-narrowed"]


def test_a_removed_enum_value_breaks_writers() -> None:
    report = subject.compare({"enum": ["a", "b"]}, {"enum": ["a"]})
    assert rules(report) == ["enum-value-removed"]
    assert "'b' is no longer allowed" in report.findings[0].message


def test_an_added_enum_value_is_safe_for_writers() -> None:
    report = subject.compare({"enum": ["a"]}, {"enum": ["a", "b"]})
    assert rules(report) == ["enum-value-added"]
    assert levels(report) == [subject.SAFE]


def test_closing_an_open_value_set_is_breaking() -> None:
    assert rules(subject.compare({}, {"enum": ["a"]})) == ["enum-added"]


def test_a_raised_minimum_is_breaking_and_a_lowered_one_is_safe() -> None:
    assert rules(subject.compare({"minimum": 1}, {"minimum": 2})) == ["minimum-increased"]
    assert rules(subject.compare({"minimum": 2}, {"minimum": 1})) == ["minimum-relaxed"]
    assert rules(subject.compare({}, {"minimum": 1})) == ["minimum-added"]
    assert rules(subject.compare({"minimum": 1}, {})) == ["minimum-removed"]


def test_a_lowered_maximum_is_breaking_and_a_raised_one_is_safe() -> None:
    assert rules(subject.compare({"maximum": 9}, {"maximum": 2})) == ["maximum-decreased"]
    assert rules(subject.compare({"maximum": 2}, {"maximum": 9})) == ["maximum-relaxed"]
    assert rules(subject.compare({}, {"maximum": 9})) == ["maximum-added"]


def test_string_length_bounds_follow_the_same_direction() -> None:
    assert rules(subject.compare({"minLength": 1}, {"minLength": 2})) == ["minLength-increased"]
    assert rules(subject.compare({"minLength": 2}, {"minLength": 1})) == ["minLength-relaxed"]
    assert rules(subject.compare({"maxLength": 9}, {"maxLength": 2})) == ["maxLength-decreased"]
    assert rules(subject.compare({"maxLength": 2}, {"maxLength": 9})) == ["maxLength-relaxed"]


def test_a_new_required_member_breaks_every_existing_writer() -> None:
    report = subject.compare({"required": ["a"]}, {"required": ["a", "b"]})
    assert rules(report) == ["required-added"]
    assert "'b' is required now" in report.findings[0].message


def test_a_dropped_requirement_is_safe() -> None:
    assert rules(subject.compare({"required": ["a", "b"]}, {"required": ["a"]})) == [
        "required-relaxed"
    ]


def test_removing_a_property_breaks_readers() -> None:
    report = subject.compare({"properties": {"a": {}, "b": {}}}, {"properties": {"a": {}}})
    assert report.findings[0].path == "$.b"
    assert report.findings[0].rule == "property-removed"
    assert "gets nothing" in report.findings[0].message


def test_adding_a_property_is_safe() -> None:
    report = subject.compare({"properties": {"a": {}}}, {"properties": {"a": {}, "b": {}}})
    assert rules(report) == ["property-added"]
    assert report.findings[0].path == "$.b"


def test_closing_additional_properties_breaks_documents_that_carried_extras() -> None:
    report = subject.compare({"additionalProperties": True}, {"additionalProperties": False})
    assert rules(report) == ["additional-properties-closed"]
    assert levels(report) == [subject.BREAKING]


def test_opening_additional_properties_is_safe() -> None:
    report = subject.compare({"additionalProperties": False}, {})
    assert rules(report) == ["additional-properties-opened"]


def test_a_nested_change_is_walked_not_just_the_top_level() -> None:
    old = {"properties": {"a": {"properties": {"b": {"type": "string"}}}}}
    new = {"properties": {"a": {"properties": {"b": {"type": "integer"}}}}}
    report = subject.compare(old, new)
    assert report.findings[0].path == "$.a.b"
    assert rules(report) == ["type-changed"]


def test_a_changed_pattern_is_risky_because_nobody_can_decide_it() -> None:
    report = subject.compare({"pattern": "^a"}, {"pattern": "^b"})
    assert rules(report) == ["pattern-changed"]
    assert levels(report) == [subject.RISKY]
    assert rules(subject.compare({}, {"pattern": "^a"})) == ["pattern-added"]
    assert levels(subject.compare({"pattern": "^a"}, {})) == [subject.SAFE]


def test_a_changed_format_is_risky() -> None:
    assert rules(subject.compare({"format": "email"}, {"format": "uuid"})) == ["format-changed"]


def test_a_changed_const_is_breaking() -> None:
    report = subject.compare({"const": "a"}, {"const": "b"})
    assert rules(report) == ["const-changed"]
    assert levels(report) == [subject.BREAKING]


def test_a_default_is_a_behaviour_change_so_it_is_risky() -> None:
    assert rules(subject.compare({}, {"default": 1})) == ["default-added"]
    assert rules(subject.compare({"default": 1}, {"default": 2})) == ["default-changed"]


def test_a_deprecation_is_risky() -> None:
    assert rules(subject.compare({}, {"deprecated": True})) == ["deprecated"]


def test_documentation_keys_are_ignored() -> None:
    old = {"description": "a", "title": "x", "examples": [1], "$comment": "old"}
    new = {"description": "b", "title": "y", "examples": [2], "$comment": "new"}
    assert subject.compare(old, new).findings == []


def test_findings_are_sorted_so_two_runs_print_the_same_report() -> None:
    old = {"properties": {"b": {"type": "string"}, "a": {"maximum": 9}}, "required": ["a"]}
    new = {"properties": {"b": {"type": "integer"}, "a": {"maximum": 2}}, "required": ["a", "c"]}
    report = subject.compare(old, new)
    assert [(finding.path, finding.rule) for finding in report.findings] == [
        ("$", "required-added"),
        ("$.a", "maximum-decreased"),
        ("$.b", "type-changed"),
    ]


def test_the_verdict_is_the_worst_finding() -> None:
    assert subject.compare({}, {"type": "string"}).verdict == subject.BREAKING
    assert subject.compare({}, {"pattern": "^a"}).verdict == subject.RISKY
    assert subject.compare({}, {}).verdict == "compatible"


def test_a_risky_change_fails_only_under_strict() -> None:
    report = subject.compare({}, {"default": 1})
    assert not report.fails()
    assert report.fails(strict=True)


def test_an_unchanged_schema_says_so_in_one_line() -> None:
    report = subject.compare({"type": "string"}, {"type": "string"})
    assert report.lines() == ["no change that affects a document or a reader"]


def test_the_payload_carries_the_counts() -> None:
    report = subject.compare({"properties": {"a": {}, "b": {}}}, {"properties": {"a": {}}})
    payload = report.as_dict()
    assert payload["verdict"] == subject.BREAKING
    assert payload["counts"] == {subject.BREAKING: 1, subject.RISKY: 0, subject.SAFE: 0}
    assert payload["findings"][0]["path"] == "$.b"


def test_the_summary_line_names_the_verdict(v1: dict, v2: dict) -> None:
    report = subject.compare(v1, v2)
    assert report.lines()[-1] == "5 breaking, 0 risky, 1 safe -> breaking"


def test_the_shipped_fixtures_are_what_they_claim(v1: dict, v2: dict, v3: dict, v4: dict) -> None:
    assert len(subject.compare(v1, v2).breaking) == 5
    assert subject.compare(v1, v3).breaking == []
    assert [finding.rule for finding in subject.compare(v1, v4).risky] == [
        "format-changed",
        "pattern-changed",
        "deprecated",
        "default-added",
    ]


def test_a_ref_is_resolved_before_comparing() -> None:
    old = {"$defs": {"a": {"type": "string"}}, "properties": {"x": {"$ref": "#/$defs/a"}}}
    new = {"$defs": {"a": {"type": "integer"}}, "properties": {"x": {"$ref": "#/$defs/a"}}}
    report = subject.compare(old, new)
    assert report.findings[0].path == "$.x"
    assert rules(report) == ["type-changed"]
