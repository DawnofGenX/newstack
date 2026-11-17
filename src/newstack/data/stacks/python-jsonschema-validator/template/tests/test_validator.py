from jsonschema import FormatChecker

from {{ package_name }}.validator import validate_document


def test_valid_document():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"]}
    assert validate_document({"n": 5}, schema) == []


def test_multiple_errors_all_reported():
    schema = {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    errs = validate_document({"name": 123, "age": "x"}, schema)
    paths = {e["path"] for e in errs}
    assert "/name" in paths
    assert "/age" in paths


def test_custom_format_without_network():
    fc = FormatChecker()

    @fc.checks("even")
    def _even(value):
        return isinstance(value, int) and value % 2 == 0

    schema = {"type": "object", "properties": {"value": {"type": "integer", "format": "even"}}}
    errs = validate_document({"value": 3}, schema, format_checker=fc)
    assert any(e["path"] == "/value" for e in errs)