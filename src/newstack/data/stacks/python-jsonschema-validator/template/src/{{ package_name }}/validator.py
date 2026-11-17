"""jsonschema validation collecting ALL errors with JSON Pointer paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import validators


def _pointer(path: list[Any] | tuple[Any, ...]) -> str:
    if not path:
        return ""
    parts: list[str] = []
    for seg in path:
        s = str(seg)
        s = s.replace("~", "~0").replace("/", "~1")
        parts.append(s)
    return "/" + "/".join(parts)


def validate_document(instance: Any, schema: Any, format_checker: Any = None) -> list[dict[str, str]]:
    """Return a list of error dicts with 'path' (JSON Pointer) and 'message'."""
    validator_cls = validators.validator_for(schema)
    validator = validator_cls(schema, format_checker=format_checker)
    errors: list[dict[str, str]] = []
    for err in validator.iter_errors(instance):
        errors.append({"path": _pointer(list(err.absolute_path)), "message": err.message})
    errors.sort(key=lambda e: e["path"])
    return errors


def is_valid(instance: Any, schema: Any, format_checker: Any = None) -> bool:
    return not validate_document(instance, schema, format_checker)


def render_report(errors: list[dict[str, str]]) -> str:
    if not errors:
        return "valid: no errors"
    lines = [f"{len(errors)} error(s):"]
    for e in errors:
        lines.append(f"  {e['path'] or '/'}: {e['message']}")
    return "\n".join(lines)


def load_json(path: str | Path) -> Any:
    with Path(path).open() as f:
        return json.load(f)