"""Merge the layers in order, and remember where every value came from.

The merge is a fold over the layers rather than a chain of ``if`` statements, so
adding a layer is one line and the precedence order is a list you can read.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import sources, spec
from .spec import ConfigError, Key

DEFAULT_SOURCE = "default"
LAYER_ORDER = ("file", "env", "flag")


@dataclass(frozen=True)
class Value:
    key: Key
    value: Any
    source: str
    origin: str

    def shown(self, reveal: bool = False) -> Any:
        """A secret is masked unless someone asked to see it."""
        if self.key.secret and not reveal:
            return "***"
        return self.value


@dataclass(frozen=True)
class Resolution:
    values: dict[str, Value]
    problems: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.problems

    def get(self, name: str) -> Value:
        if name not in spec.BY_NAME:
            raise ConfigError(f"unknown setting {name!r}; run `show` to list them")
        try:
            return self.values[name]
        except KeyError:
            raise ConfigError(f"{name} did not resolve; run `check` to see why") from None

    def changed(self) -> list[Value]:
        return [value for value in self.values.values() if value.source != DEFAULT_SOURCE]

    def default_secrets(self) -> list[Value]:
        return [
            value
            for value in self.values.values()
            if value.key.secret and value.source == DEFAULT_SOURCE
        ]


def resolve(
    config: Path | None = None,
    environ: Mapping[str, str] | None = None,
    flags: Iterable[str] = (),
    prefix: str = "APP",
) -> Resolution:
    problems: list[str] = []
    layers: list[tuple[str, sources.Layer]] = []

    if config is not None:
        layer, found = sources.from_file(config)
        problems.extend(found)
        layers.append(("file", layer))

    layer, found = sources.from_env(os.environ if environ is None else environ, prefix)
    problems.extend(found)
    layers.append(("env", layer))

    layer, found = sources.from_flags(list(flags))
    problems.extend(found)
    layers.append(("flag", layer))

    values: dict[str, Value] = {}
    for key in spec.KEYS:
        chosen: tuple[Any, str] | None = None
        source = DEFAULT_SOURCE
        for name, layer in layers:
            if key.name in layer:
                chosen, origin = layer[key.name]
                source = name
        if chosen is None:
            if key.required:
                problems.append(
                    f"{key.name} is required and no layer supplies it "
                    f"(set {key.env_name(prefix)} or add {key.name} = ... to the config file)"
                )
                continue
            values[key.name] = Value(key, key.default, DEFAULT_SOURCE, "default")
            continue
        try:
            values[key.name] = Value(key, sources.parse(key, chosen, origin), source, origin)
        except ConfigError as error:
            problems.append(str(error))
    return Resolution(values, tuple(problems))
