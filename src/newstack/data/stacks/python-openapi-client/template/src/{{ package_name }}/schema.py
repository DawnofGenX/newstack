"""The slice of JSON Schema an OpenAPI 3.1 document actually uses here.

Every function returns problems as strings instead of raising, so a drift report
can list everything that disagrees rather than stopping at the first member.
"""

from __future__ import annotations

from typing import Any

SCALARS = ("string", "integer", "number", "boolean", "null", "object", "array")


class SchemaError(ValueError):
    """The document refers to something that is not there."""


def type_name(value: object) -> str:
    """The JSON type of a Python value.

    `bool` is a subclass of `int` in Python, so `isinstance(True, int)` is true and a
    naive validator accepts `true` where the schema says integer. Booleans are named
    first for exactly that reason.
    """
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


def _matches(value: object, wanted: str) -> bool:
    if wanted == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if wanted == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if wanted == "boolean":
        return isinstance(value, bool)
    if wanted == "null":
        return value is None
    if wanted == "string":
        return isinstance(value, str)
    if wanted == "array":
        return isinstance(value, list)
    if wanted == "object":
        return isinstance(value, dict)
    raise SchemaError(f"unknown JSON type {wanted!r}")


def same_value(left: object, right: object) -> bool:
    """Equality that does not confuse `true` with `1`.

    `True == 1` is true in Python, so `value in enum` would accept a boolean where the
    enum lists an integer.
    """
    return type_name(left) == type_name(right) and left == right


def resolve(document: dict[str, Any], ref: str) -> dict[str, Any]:
    """Resolve a local JSON pointer such as `#/components/schemas/Note`."""
    if not ref.startswith("#/"):
        raise SchemaError(f"only local references are supported, got {ref!r}")
    node: Any = document
    for raw in ref[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or token not in node:
            raise SchemaError(f"cannot resolve {ref!r}: {token!r} is not there")
        node = node[token]
    if not isinstance(node, dict):
        raise SchemaError(f"{ref!r} does not point at a schema")
    return node


def _child(path: str, member: str) -> str:
    return f"{path}.{member}"


def _index(path: str, position: int) -> str:
    return f"{path}[{position}]"


def _declared_types(schema: dict[str, Any]) -> list[str]:
    declared = schema.get("type")
    if isinstance(declared, str):
        allowed = [declared]
    elif isinstance(declared, list):
        allowed = [str(item) for item in declared]
    else:
        allowed = []
    if schema.get("nullable") is True and "null" not in allowed:
        allowed = [*allowed, "null"]
    return allowed


def validate(
    value: object,
    schema: dict[str, Any],
    document: dict[str, Any],
    path: str = "$",
) -> list[str]:
    """Every way `value` disagrees with `schema`, as `$....` problems."""
    if "$ref" in schema:
        return validate(value, resolve(document, str(schema["$ref"])), document, path)

    problems: list[str] = []
    allowed = _declared_types(schema)

    if allowed and not any(_matches(value, wanted) for wanted in allowed):
        joined = " or ".join(allowed)
        problems.append(f"{path}: expected {joined}, got {type_name(value)}")
        return problems

    if "const" in schema and not same_value(value, schema["const"]):
        problems.append(f"{path}: expected the constant {schema['const']!r}, got {value!r}")

    enum = schema.get("enum")
    if isinstance(enum, list) and not any(same_value(value, option) for option in enum):
        shown = ", ".join(sorted(repr(option) for option in enum))
        problems.append(f"{path}: {value!r} is not one of {shown}")

    for keyword in ("anyOf", "oneOf"):
        branches = schema.get(keyword)
        fits = isinstance(branches, list) and branches
        if fits and not any(not validate(value, branch, document, path) for branch in branches):
            problems.append(f"{path}: matches none of the {keyword} schemas")

    if isinstance(value, str):
        shortest = schema.get("minLength")
        longest = schema.get("maxLength")
        if isinstance(shortest, int) and len(value) < shortest:
            problems.append(f"{path}: shorter than {shortest} characters")
        if isinstance(longest, int) and len(value) > longest:
            problems.append(f"{path}: longer than {longest} characters")

    if isinstance(value, int | float) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, int | float) and value < minimum:
            problems.append(f"{path}: {value} is below the minimum {minimum}")
        if isinstance(maximum, int | float) and value > maximum:
            problems.append(f"{path}: {value} is above the maximum {maximum}")

    if isinstance(value, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for position, item in enumerate(value):
                problems.extend(validate(item, items, document, _index(path, position)))
        shortest = schema.get("minItems")
        longest = schema.get("maxItems")
        if isinstance(shortest, int) and len(value) < shortest:
            problems.append(f"{path}: fewer than {shortest} items")
        if isinstance(longest, int) and len(value) > longest:
            problems.append(f"{path}: more than {longest} items")

    if isinstance(value, dict):
        required = schema.get("required")
        if isinstance(required, list):
            for member in required:
                if member not in value:
                    problems.append(f"{path}: missing required member {member!r}")
        properties = schema.get("properties")
        known = properties if isinstance(properties, dict) else {}
        for member, member_value in value.items():
            member_schema = known.get(member)
            if isinstance(member_schema, dict):
                where = _child(path, member)
                problems.extend(validate(member_value, member_schema, document, where))
            elif schema.get("additionalProperties") is False:
                problems.append(f"{path}: unexpected member {member!r}")

    return problems
