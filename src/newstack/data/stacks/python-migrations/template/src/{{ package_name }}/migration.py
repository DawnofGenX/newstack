"""A migration is a file, and a file has bytes: the checksum is over those bytes.

Two decisions are load-bearing.

The id comes from the filename (``0002_add_pinned.sql`` -> ``0002``) instead of
from a number inside the file, because the order migrations run in has to be
visible with ``ls``. A file renamed is a file reordered; a number in a comment is
not.

The checksum is taken over the raw bytes rather than over the parsed SQL, because
a trailing newline, a changed quote style or a re-indented statement all change
what runs. A ledger that only remembers "0002 ran" cannot tell you that the
``0002`` in front of you is not the ``0002`` that ran.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

NAME = re.compile(r"^(?P<migration_id>[0-9]+)_(?P<slug>[a-z0-9_]+)\.sql$")


class MigrationError(ValueError):
    """The migrations directory, or the request against it, cannot be served."""


@dataclass(frozen=True)
class Migration:
    """One file on disk: its identity, its bytes, and its SQL."""

    migration_id: str
    slug: str
    sql: str
    checksum: str
    path: Path

    @property
    def label(self) -> str:
        """The filename without the extension, e.g. ``0002_add_pinned``."""
        return f"{self.migration_id}_{self.slug}"

    @property
    def number(self) -> int:
        """The id as an integer, so ``10`` sorts after ``9`` and not before it."""
        return int(self.migration_id)

    def short(self) -> str:
        """A checksum prefix short enough to read in a table and long enough to trust."""
        return self.checksum[:12]

    @classmethod
    def from_path(cls, path: Path) -> Migration:
        """Read one file, refusing a name that cannot be ordered."""
        match = NAME.match(path.name)
        if match is None:
            raise MigrationError(
                f"{path.name}: expected <number>_<lower_snake_case>.sql, "
                "for example 0002_add_pinned.sql"
            )
        raw = path.read_bytes()
        sql = raw.decode("utf-8")
        if not sql.strip():
            raise MigrationError(f"{path.name}: the file is empty")
        return cls(
            migration_id=match.group("migration_id"),
            slug=match.group("slug"),
            sql=sql,
            checksum=hashlib.sha256(raw).hexdigest(),
            path=path,
        )


def load(directory: str | Path) -> list[Migration]:
    """Every migration in `directory`, ordered the way they must run.

    A gap in the numbering is allowed: a migration that was reverted before it
    ever shipped leaves one behind, and refusing to start would punish history.
    A duplicate is not allowed, because two files that claim the same position
    cannot both be the second migration.
    """
    folder = Path(directory)
    if not folder.is_dir():
        raise MigrationError(f"{folder}: not a directory")
    migrations = [Migration.from_path(path) for path in sorted(folder.glob("*.sql"))]
    seen: dict[int, Migration] = {}
    for migration in migrations:
        first = seen.get(migration.number)
        if first is not None:
            raise MigrationError(
                f"{migration.number:04d} is claimed twice: "
                f"{first.path.name} and {migration.path.name}"
            )
        seen[migration.number] = migration
    return sorted(migrations, key=lambda migration: migration.number)
