"""Reading the flags file: [[flag]] tables, and every mistake reported at once."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .model import Flag, FlagSet, InputError

KNOWN = ("name", "enabled", "rollout", "salt", "targets")


def _flag_of(table: dict[str, Any], where: str) -> Flag:
    unknown = sorted(set(table) - set(KNOWN))
    if unknown:
        raise InputError(
            f"{where}: unknown key(s) {', '.join(unknown)}; known keys are {', '.join(KNOWN)}"
        )
    targets = table.get("targets", [])
    if not isinstance(targets, list) or not all(isinstance(item, str) for item in targets):
        raise InputError(f"{where}: targets must be a list of user ids")
    return Flag(
        name=table.get("name", ""),
        enabled=table.get("enabled", True),
        rollout=table.get("rollout", 0),
        salt=table.get("salt", ""),
        targets=frozenset(targets),
    )


def load(path: Path) -> FlagSet:
    try:
        text = path.read_bytes()
    except OSError as error:
        raise InputError(f"cannot read {path}: {error}") from error
    try:
        document = tomllib.loads(text.decode())
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise InputError(f"{path} is not valid TOML: {error}") from error
    tables = document.get("flag", [])
    if not isinstance(tables, list):
        raise InputError(f"{path}: [[flag]] must be a list of tables")
    problems: list[str] = []
    flags: list[Flag] = []
    for index, table in enumerate(tables):
        where = f"{path} flag #{index + 1}"
        if not isinstance(table, dict):
            problems.append(f"{where}: expected a table")
            continue
        try:
            flags.append(_flag_of(table, where))
        except InputError as error:
            problems.append(str(error))
    if problems:
        raise InputError("; ".join(problems))
    return FlagSet.of(flags)
