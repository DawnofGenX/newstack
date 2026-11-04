"""Licence texts a generated project can ship.

The bodies live in ``data/licenses`` as plain text rather than Python strings so
they can be byte-compared with the ones the stack templates carry (that is how
the drift guard in the tests works) and so adding a licence stays a data change.

``mit.txt`` is the exact text every template already ships, so selecting the
default licence reproduces, byte for byte, the ``LICENSE`` newstack has always
written. Templates therefore keep their own copy; the registry is what
``--license`` and ``--license none`` act on.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parent / "data" / "licenses"

FILE_NAME = "LICENSE"
DEFAULT = "mit"
NONE = "none"


class LicenseError(Exception):
    """The requested licence is not one newstack can generate."""


@dataclass(frozen=True)
class License:
    key: str
    title: str
    spdx: str
    file: str


LICENSES: tuple[License, ...] = (
    License(key="mit", title="MIT", spdx="MIT", file="mit.txt"),
    License(key="apache-2.0", title="Apache 2.0", spdx="Apache-2.0", file="apache-2.0.txt"),
    License(key="bsd-3", title="BSD 3-Clause", spdx="BSD-3-Clause", file="bsd-3.txt"),
)

BY_KEY: dict[str, License] = {license.key: license for license in LICENSES}

#: Values ``--license`` accepts, in help-text order.
CHOICES: tuple[str, ...] = tuple(BY_KEY) + (NONE,)


def get(key: str) -> License:
    """Look up a licence by its ``--license`` name."""
    try:
        return BY_KEY[key]
    except KeyError:
        raise LicenseError(
            f"unknown licence '{key}': choose from {', '.join(CHOICES)}"
        ) from None


@cache
def text(key: str) -> str:
    """The licence body, still carrying its ``{{ year }}``/``{{ author }}`` placeholders."""
    license = get(key)
    try:
        return (DATA_ROOT / license.file).read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - only when the package is broken
        raise LicenseError(f"licence text for '{key}' is missing: {exc}") from exc
