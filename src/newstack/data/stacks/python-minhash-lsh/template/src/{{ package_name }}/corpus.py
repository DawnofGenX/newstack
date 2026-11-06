"""A corpus whose similarities are known, so errors can be measured rather than guessed."""

from __future__ import annotations

from .rng import Rng

WORDS = [f"w{number:03d}" for number in range(400)]


def document(seed: int, *, words: int = 80, vocabulary: int = 400) -> str:
    """A deterministic pseudo-document of `words` words."""
    if words < 1:
        raise ValueError(f"a document needs at least one word, not {words}")
    if not 1 <= vocabulary <= len(WORDS):
        raise ValueError(f"a vocabulary of {vocabulary} words is outside 1..{len(WORDS)}")
    rng = Rng(seed * 7919 + 13)
    return " ".join(WORDS[rng.below(vocabulary)] for _ in range(words))


def variant(text: str, *, replace_every: int, seed: int) -> str:
    """Replace every `replace_every`-th word, which sets the similarity by construction."""
    if replace_every < 1:
        raise ValueError(f"replace_every needs to be at least 1, not {replace_every}")
    words = text.split()
    rng = Rng(seed * 104_729 + 7)
    edited = [
        WORDS[rng.below(len(WORDS))] if position % replace_every == 0 else word
        for position, word in enumerate(words)
    ]
    return " ".join(edited)


def pair(*, replace_every: int, words: int = 120, seed: int = 3) -> tuple[str, str, str]:
    """A base document, a variant, and a name for each."""
    base = document(seed, words=words)
    edited = variant(base, replace_every=replace_every, seed=seed)
    return base, edited, f"pair-{replace_every}"


def family(*, count: int, duplicates: int, replace_every: int = 8) -> list[tuple[str, str]]:
    """`count` documents, of which `duplicates` are near-copies of an earlier one."""
    if count < 1:
        raise ValueError(f"a corpus needs at least one document, not {count}")
    if duplicates < 0:
        raise ValueError(f"duplicate count cannot be negative, not {duplicates}")
    originals = [document(1_000 + number) for number in range(max(1, count - duplicates))]
    documents = [(f"doc-{number:03d}", text) for number, text in enumerate(originals)]
    for index in range(duplicates):
        source = originals[index % len(originals)]
        documents.append(
            (f"dup-{index:03d}", variant(source, replace_every=replace_every, seed=500 + index))
        )
    return documents
