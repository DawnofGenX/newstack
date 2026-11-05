"""Where raw values come from, and how each one becomes the declared type.

Every raw value is kept next to the place it came from. Parsing is a separate
step on purpose: one layer's bad value must not stop the others from being read,
so the user sees all of the problems in one run instead of one per attempt.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import spec
from .spec import ConfigError, Key

INTEGER = re.compile(r"^-?[0-9]+$")
DURATION = re.compile(r"^([0-9]+)(ms|s|m)$")
DURATION_UNITS = {"ms": 1, "s": 1000, "m": 60_000}
TRUE_WORDS = frozenset({"1", "true", "yes", "on"})
FALSE_WORDS = frozenset({"0", "false", "no", "off"})

# key -> (raw value, where it came from). One dict per layer.
Layer = dict[str, tuple[Any, str]]


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
    return type(value).__name__


def parse(key: Key, raw: Any, where: str) -> Any:
    """Turn one raw value into the declared type, or say exactly why not."""
    value = _parse(key, raw, where)
    _check_bounds(key, value, where)
    return value


def _parse(key: Key, raw: Any, where: str) -> Any:
    if key.kind == "string":
        if isinstance(raw, str):
            return raw
        raise ConfigError(f"{where}: expected a string, got {type_name(raw)}")

    if key.kind == "integer":
        if isinstance(raw, bool):
            raise ConfigError(f"{where}: expected an integer, got a boolean")
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str) and INTEGER.match(raw.strip()):
            return int(raw.strip())
        hint = ""
        if "_" in str(raw):
            hint = " (separators like 1_000 are not numbers anyone types in an env var)"
        raise ConfigError(f"{where}: expected an integer, got {raw!r}{hint}")

    if key.kind == "boolean":
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            folded = raw.strip().lower()
            if folded in TRUE_WORDS:
                return True
            if folded in FALSE_WORDS:
                return False
        raise ConfigError(
            f"{where}: expected a boolean (true/false/yes/no/on/off), got {raw!r}"
        )

    if key.kind == "list":
        if isinstance(raw, list | tuple):
            if all(isinstance(item, str) for item in raw):
                return tuple(item.strip() for item in raw if item.strip())
            raise ConfigError(f"{where}: expected a list of strings, got {raw!r}")
        if isinstance(raw, str):
            if raw.strip() == "":
                return ()
            items = [item.strip() for item in raw.split(",")]
            if any(item == "" for item in items):
                raise ConfigError(f"{where}: {raw!r} has an empty item between commas")
            return tuple(items)
        raise ConfigError(f"{where}: expected a list, got {type_name(raw)}")

    if key.kind == "duration":
        if isinstance(raw, str):
            match = DURATION.match(raw.strip())
            if match:
                return int(match.group(1)) * DURATION_UNITS[match.group(2)]
        raise ConfigError(f"{where}: expected a duration like 250ms, 5s or 2m, got {raw!r}")

    if key.kind == "choice":
        if isinstance(raw, str) and raw.strip().lower() in key.choices:
            return raw.strip().lower()
        raise ConfigError(
            f"{where}: expected one of {', '.join(key.choices)}, got {raw!r}"
        )

    raise ConfigError(f"{where}: setting {key.name} has the unknown kind {key.kind!r}")


def _check_bounds(key: Key, value: Any, where: str) -> None:
    if key.kind != "integer":
        return
    if key.minimum is not None and value < key.minimum:
        raise ConfigError(f"{where}: {value} is below the minimum of {key.minimum}")
    if key.maximum is not None and value > key.maximum:
        raise ConfigError(f"{where}: {value} is above the maximum of {key.maximum}")


def load_file(path: Path) -> dict[str, Any]:
    """Flatten TOML tables into dotted keys: ``[server] port = 9000`` -> ``server.port``."""
    try:
        text = path.read_text()
    except OSError as error:
        raise ConfigError(f"cannot read {path}: {error.strerror or error}") from error
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path} is not valid TOML: {error}") from error
    return _flatten(document)


def _flatten(table: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for name, value in table.items():
        dotted = f"{prefix}{name}"
        if isinstance(value, dict):
            flat.update(_flatten(value, f"{dotted}."))
        else:
            flat[dotted] = value
    return flat


def from_file(path: Path) -> tuple[Layer, list[str]]:
    """A key the schema does not define is a typo, not an extension."""
    flat = load_file(path)
    layer: Layer = {}
    problems: list[str] = []
    for name, value in flat.items():
        if name not in spec.BY_NAME:
            problems.append(
                f"file {path} at {name}: no setting answers to that name "
                "(check the spelling, and use [section] key = value for nesting)"
            )
            continue
        layer[name] = (value, f"file {path}")
    return layer, problems


def from_env(environ: Mapping[str, str], prefix: str) -> tuple[Layer, list[str]]:
    """Every variable carrying the prefix is either a known setting or a typo."""
    known = spec.env_names(prefix)
    layer: Layer = {}
    problems: list[str] = []
    for name in sorted(environ):
        if not name.startswith(prefix + "_"):
            continue
        key = known.get(name)
        if key is None:
            example = f"{prefix}_SERVER__PORT"
            problems.append(
                f"env {name}: no setting answers to that name "
                f"(nesting uses a double underscore, e.g. {example})"
            )
            continue
        layer[key.name] = (environ[name], f"env {name}")
    return layer, problems


def from_flags(pairs: list[str]) -> tuple[Layer, list[str]]:
    """``--set key=value``: the highest layer, and never a file."""
    layer: Layer = {}
    problems: list[str] = []
    for pair in pairs:
        name, separator, raw = pair.partition("=")
        if not separator or not name.strip():
            problems.append(f"flag --set {pair}: expected key=value")
            continue
        name = name.strip()
        if name not in spec.BY_NAME:
            problems.append(f"flag --set {name}: no setting answers to that name")
            continue
        layer[name] = (raw, f"flag --set {name}")
    return layer, problems
