"""The settings schema: one table, and it is the only place a key is defined.

A settings module that grows an ``os.environ.get`` per key has no schema, no
provenance and no way to tell a typo from an extension. This one has all three.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

KINDS = ("string", "integer", "boolean", "list", "duration", "choice")


class ConfigError(Exception):
    """The configuration is wrong, in a way the user can fix."""


@dataclass(frozen=True)
class Key:
    name: str
    kind: str
    default: Any = None
    required: bool = False
    secret: bool = False
    choices: tuple[str, ...] = ()
    minimum: int | None = None
    maximum: int | None = None
    description: str = ""

    @property
    def has_default(self) -> bool:
        return self.default is not None

    def env_name(self, prefix: str) -> str:
        """A dot becomes a double underscore, because ``_`` is legal inside a name."""
        return f"{prefix}_{self.name.replace('.', '__').upper()}"


KEYS: tuple[Key, ...] = (
    Key("server.host", "string", "127.0.0.1", description="interface to bind"),
    Key("server.port", "integer", 8000, minimum=1, maximum=65535),
    Key("server.timeout", "duration", "5s", description="request timeout"),
    Key("db.url", "string", "sqlite:///app.db", secret=True),
    Key("db.pool_size", "integer", 5, minimum=1, maximum=64),
    Key("auth.signing_key", "string", required=True, secret=True),
    Key("auth.token_ttl", "duration", "15m"),
    Key("features.rate_limit", "boolean", True),
    Key("features.allowed_origins", "list", ("http://localhost:3000",)),
    Key("log.level", "choice", "info", choices=("debug", "info", "warning", "error")),
)

BY_NAME: dict[str, Key] = {key.name: key for key in KEYS}


def get(name: str) -> Key:
    try:
        return BY_NAME[name]
    except KeyError:
        known = ", ".join(sorted(BY_NAME))
        raise ConfigError(f"unknown setting {name!r}; known settings are: {known}") from None


def env_names(prefix: str) -> dict[str, Key]:
    return {key.env_name(prefix): key for key in KEYS}
