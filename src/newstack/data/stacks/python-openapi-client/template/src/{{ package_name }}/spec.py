"""Read an OpenAPI document and turn its paths into callable operations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

METHODS = ("get", "post", "put", "patch", "delete")


class SpecError(ValueError):
    """The document cannot be used: missing, malformed, or incomplete."""


@dataclass(frozen=True)
class Parameter:
    name: str
    location: str
    required: bool
    schema: dict[str, Any]


@dataclass(frozen=True)
class Operation:
    operation_id: str
    method: str
    path: str
    summary: str
    parameters: tuple[Parameter, ...]
    request_schema: dict[str, Any] | None
    responses: dict[str, dict[str, Any]]

    def required_parameters(self) -> tuple[str, ...]:
        return tuple(parameter.name for parameter in self.parameters if parameter.required)

    def parameter(self, name: str) -> Parameter | None:
        return next((item for item in self.parameters if item.name == name), None)


@dataclass(frozen=True)
class Spec:
    document: dict[str, Any]
    operations: dict[str, Operation]
    base_url: str

    def operation(self, operation_id: str) -> Operation:
        found = self.operations.get(operation_id)
        if found is None:
            known = ", ".join(sorted(self.operations)) or "none"
            raise SpecError(f"no operation {operation_id!r}; the document offers {known}")
        return found


def _parameters(raw: Any) -> tuple[Parameter, ...]:
    if not isinstance(raw, list):
        return ()
    collected: list[Parameter] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        schema = entry.get("schema")
        collected.append(
            Parameter(
                name=str(entry.get("name", "")),
                location=str(entry.get("in", "")),
                required=bool(entry.get("required", False)),
                schema=schema if isinstance(schema, dict) else {},
            )
        )
    return tuple(collected)


def _responses(raw: Any) -> dict[str, dict[str, Any]]:
    """Status code -> media schema. A response without a body keeps an empty schema."""
    collected: dict[str, dict[str, Any]] = {}
    if not isinstance(raw, dict):
        return collected
    for status, response in raw.items():
        schema: dict[str, Any] = {}
        if isinstance(response, dict):
            content = response.get("content")
            if isinstance(content, dict):
                for media in content.values():
                    if isinstance(media, dict) and isinstance(media.get("schema"), dict):
                        schema = media["schema"]
                        break
        collected[str(status)] = schema
    return collected


def operations_of(document: dict[str, Any]) -> dict[str, Operation]:
    paths = document.get("paths")
    if not isinstance(paths, dict) or not paths:
        raise SpecError("the document has no paths")
    operations: dict[str, Operation] = {}
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in METHODS:
            raw = path_item.get(method)
            if not isinstance(raw, dict):
                continue
            operation_id = raw.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                raise SpecError(
                    f"{method.upper()} {path} has no operationId, so it cannot be called by name"
                )
            if operation_id in operations:
                raise SpecError(f"operationId {operation_id!r} is used twice")
            body = raw.get("requestBody")
            request_schema = None
            if isinstance(body, dict):
                content = body.get("content")
                if isinstance(content, dict):
                    for media in content.values():
                        if isinstance(media, dict) and isinstance(media.get("schema"), dict):
                            request_schema = media["schema"]
                            break
            operations[operation_id] = Operation(
                operation_id=operation_id,
                method=method.upper(),
                path=str(path),
                summary=str(raw.get("summary", "")),
                parameters=_parameters(raw.get("parameters")),
                request_schema=request_schema,
                responses=_responses(raw.get("responses")),
            )
    return operations


def load(path: Path) -> Spec:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SpecError(f"cannot read the document: {error.strerror}") from error
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise SpecError(f"{path}: {error.msg} at line {error.lineno}") from error
    if not isinstance(document, dict):
        raise SpecError(f"{path}: the document must be a JSON object")
    version = str(document.get("openapi", ""))
    if not version.startswith("3."):
        raise SpecError(f"{path}: expected an OpenAPI 3.x document, found {version or 'nothing'}")
    servers = document.get("servers")
    base_url = ""
    if isinstance(servers, list) and servers and isinstance(servers[0], dict):
        base_url = str(servers[0].get("url", ""))
    return Spec(document=document, operations=operations_of(document), base_url=base_url)


def coerce(text: str, schema: dict[str, Any]) -> object:
    """A command line value is text; the schema says what it is meant to be."""
    declared = schema.get("type")
    if declared == "integer":
        try:
            return int(text, 10)
        except ValueError as error:
            raise SpecError(f"expected an integer, got {text!r}") from error
    if declared == "number":
        try:
            return float(text)
        except ValueError as error:
            raise SpecError(f"expected a number, got {text!r}") from error
    if declared == "boolean":
        lowered = text.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
        raise SpecError(f"expected a boolean, got {text!r}")
    return text


def build_url(base_url: str, operation: Operation, values: dict[str, object]) -> str:
    """Fill `{id}` from the values, percent-encoding every one of them.

    Without encoding, an id of `a/b` silently becomes two path segments and `a?b=1`
    becomes a query string, so the request lands somewhere the spec never described.
    """
    path = operation.path
    query: list[tuple[str, str]] = []
    declared = {parameter.name for parameter in operation.parameters}
    leftover = sorted(set(values) - declared)
    if leftover:
        offered = ", ".join(parameter.name for parameter in operation.parameters) or "none"
        raise SpecError(
            f"{operation.operation_id} takes no parameter "
            f"{', '.join(leftover)}; it offers {offered}"
        )
    for parameter in operation.parameters:
        if parameter.name not in values:
            if parameter.required:
                raise SpecError(f"{operation.operation_id} needs --param {parameter.name}")
            continue
        value = values[parameter.name]
        if parameter.location == "path":
            path = path.replace("{" + parameter.name + "}", quote(str(value), safe=""))
        elif parameter.location == "query":
            query.append((parameter.name, str(value)))
    if "{" in path:
        missing = path[path.index("{") + 1 : path.index("}")]
        raise SpecError(f"{operation.operation_id} needs --param {missing}")
    url = base_url.rstrip("/") + path
    if query:
        url = f"{url}?{urlencode(query)}"
    return url
