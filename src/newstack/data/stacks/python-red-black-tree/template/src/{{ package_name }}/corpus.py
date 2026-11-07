"""Key lists in, snapshots out: the file the smoke test builds on.

One bounded integer per line; blank lines and ``#`` comments are
skipped. A list is read whole or refused by name, so a tree is never
half-fed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .keys import KeyError, ensure_key

DEFAULT_SEED = 17


class CorpusError(ValueError):
    """A key list was asked for what it is not."""

    __slots__ = ()


def parse_key(text: str) -> int:
    """One bounded integer in, the key out; noise is refused by name."""
    try:
        return ensure_key(int(text.strip()))
    except (ValueError, KeyError) as error:
        raise CorpusError(f"not a key: {text.strip()!r} holds {error}") \
            from error


def load_keys(path: str) -> list[int]:
    """The keys on a file, in the order they are written."""
    try:
        with open(path, encoding="utf-8") as handle:
            body = handle.read()
    except OSError as error:
        raise CorpusError(f"no such key list: {error}") from error
    found: list[int] = []
    for line in body.splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        found.append(parse_key(text))
    return found


def write_keys(keys: list[int], path: str) -> None:
    """Write the keys, one per line, the way load reads them back."""
    with open(path, "w", encoding="utf-8") as handle:
        for key in keys:
            handle.write(f"{ensure_key(key)}\n")


def synthetic(count: int, seed: int = DEFAULT_SEED,
              span: int = 60) -> list[int]:
    """Distinct bounded keys, deterministic under a seed."""
    if count <= 0:
        raise CorpusError("a corpus of zero is no corpus")
    if span < count:
        raise CorpusError("the span cannot hold that many distinct keys")
    import random

    rng = random.Random(seed)
    return rng.sample(range(-span, span), count)


@dataclass(frozen=True)
class Snapshot:
    """A corpus and the seed that wrote it, kept as one JSON line."""

    keys: tuple[int, ...]
    seed: int

    def dumps(self) -> str:
        import json

        return json.dumps({"keys": list(self.keys), "seed": self.seed})

    @classmethod
    def loads(cls, body: str) -> Snapshot:
        import json

        try:
            payload = json.loads(body)
            body_keys = payload["keys"]
            body_seed = payload["seed"]
        except (LookupError, TypeError, ValueError) as error:
            raise CorpusError(f"half a snapshot is no snapshot: {error}") \
                from error
        try:
            keys = tuple(ensure_key(key) for key in body_keys)
            seed = int(body_seed)
        except (TypeError, ValueError) as error:
            raise CorpusError(f"half a snapshot is no snapshot: {error}") \
                from error
        return cls(keys, seed)
