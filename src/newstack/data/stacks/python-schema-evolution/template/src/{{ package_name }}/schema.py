"""A JSON Schema loader and the small validator the rules are proven against.

The validator exists so the compatibility rules can be checked instead of
asserted: a rule that says "a document that passed the old schema fails the new
one" has to name such a document, and this is what decides it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

INPUT_VERSION = "https://json-schema.org/draft/2020-12/schema"
TYPES = ("null", "boolean", "object", "array", "number", "string", "integer")


class SchemaError(ValueError):
    """The file is not a schema this tool can read."""


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def matches_type(value: Any, wanted: str) -> bool:
    actual = type_name(value)
    if wanted == "number":
        return actual in ("number", "integer")
    return actual == wanted


def resolve(document: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaError(f"only local $ref is supported, got {ref!r}")
    node: Any = document
    for part in ref[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or key not in node:
            raise SchemaError(f"$ref {ref!r} does not resolve")
        node = node[key]
    if not isinstance(node, dict):
        raise SchemaError(f"$ref {ref!r} is not an object")
    return node


def deref(document: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    seen = 0
    while "$ref" in schema:
        schema = resolve(document, str(schema["$ref"]))
        seen += 1
        if seen > 16:
            raise SchemaError("$ref chain is too deep (a cycle?)")
    return schema


def types_of(schema: dict[str, Any]) -> set[str] | None:
    """The types a value may have, or None for "any type"."""
    declared = schema.get("type")
    if declared is None:
        return None
    if isinstance(declared, str):
        return {declared}
    return {str(item) for item in declared}


def load(path: Path | str) -> dict[str, Any]:
    try:
        text = Path(path).read_text()
    except OSError as error:
        raise SchemaError(f"cannot read {path}: {error}") from error
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise SchemaError(f"{path} is not JSON: {error}") from error
    if not isinstance(document, dict):
        raise SchemaError(f"{path} is not a JSON object")
    if "$schema" not in document:
        raise SchemaError(f"{path} has no $schema; this is a schema, not a sample")
    return document


def validate(
    document: dict[str, Any], schema: dict[str, Any], value: Any, path: str = "$"
) -> list[str]:
    """Every way `value` fails `schema`, in the subset the fixtures use."""
    schema = deref(document, schema)
    problems: list[str] = []
    allowed = types_of(schema)
    if allowed is not None and not any(matches_type(value, wanted) for wanted in allowed):
        names = ", ".join(sorted(allowed))
        return [f"{path}: expected {names}, got {type_name(value)}"]

    if "const" in schema and value != schema["const"]:
        problems.append(f"{path}: expected {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        problems.append(f"{path}: {value!r} is not one of {schema['enum']!r}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            problems.append(f"{path}: shorter than {schema['minLength']}")
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            problems.append(f"{path}: longer than {schema['maxLength']}")
        if "pattern" in schema and not re.search(str(schema["pattern"]), value):
            problems.append(f"{path}: {value!r} does not match {schema['pattern']!r}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            problems.append(f"{path}: below the minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            problems.append(f"{path}: above the maximum {schema['maximum']}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                problems.append(f"{path}: missing required member {name!r}")
        for name, member in value.items():
            child = f"{path}.{name}"
            if name in properties:
                problems.extend(validate(document, properties[name], member, child))
            elif schema.get("additionalProperties") is False:
                problems.append(f"{child}: unexpected member {name!r}")
            elif isinstance(schema.get("additionalProperties"), dict):
                problems.extend(validate(document, schema["additionalProperties"], member, child))
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            problems.extend(validate(document, schema["items"], item, f"{path}[{index}]"))
    return problems
