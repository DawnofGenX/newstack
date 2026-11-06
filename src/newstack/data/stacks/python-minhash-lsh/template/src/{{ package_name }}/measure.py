"""Recall, precision and candidate reduction, measured against the exact answer."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .lsh import Bands
from .minhash import MinHash
from .shingles import jaccard, shingles


@dataclass(frozen=True)
class Report:
    """What a banding found, against every pair the exact similarity would pick."""

    documents: int
    width: int
    bands: Bands
    threshold: float
    true_pairs: int
    all_pairs: int
    candidates: int
    found: int
    missed: int
    spurious: int
    verified: int

    @property
    def recall(self) -> float:
        return 1.0 if self.true_pairs == 0 else self.found / self.true_pairs

    @property
    def precision(self) -> float:
        return 1.0 if self.verified == 0 else self.found / self.verified

    @property
    def reduction(self) -> float:
        return 1.0 - self.candidates / self.all_pairs if self.all_pairs else 1.0

    def lines(self) -> list[str]:
        return [
            f"documents    {self.documents} ({self.all_pairs:,} possible pairs)",
            f"banding      {self.bands.describe()}, width {self.width}",
            f"candidates   {self.candidates:,} pair(s), {self.reduction:.1%} of the space "
            "never compared",
            f"exact        {self.true_pairs:,} pair(s) at or above {self.threshold:.2f}",
            f"found        {self.found:,} of {self.true_pairs:,}, recall {self.recall:.1%}",
            f"verified     {self.verified:,} candidate(s) survive the estimate, "
            f"{self.spurious:,} do not",
            f"precision    {self.precision:.1%}",
        ]


def evaluate(
    documents: list[tuple[str, str]],
    *,
    width: int = 128,
    bands: Bands | None = None,
    threshold: float = 0.8,
    shingle_size: int = 5,
) -> Report:
    """Run banding and verification over a corpus and compare with the exact pairs."""
    if len(documents) < 2:
        raise ValueError("a corpus needs at least two documents")
    names = [name for name, _ in documents]
    if len(set(names)) != len(names):
        raise ValueError("two documents share a name, so a pair could not be attributed")
    sets = {name: shingles(text, shingle_size) for name, text in documents}
    scheme = MinHash(width, shingle_size=shingle_size)
    signatures = {name: scheme.signature_of(items) for name, items in sets.items()}
    chosen = bands if bands is not None else Bands(width, 1)
    if chosen.width > width:
        raise ValueError(
            f"the banding needs {chosen.width} positions but the signatures hold {width}"
        )
    truth = {
        (left, right)
        for left, right in combinations(sorted(names), 2)
        if jaccard(sets[left], sets[right]) >= threshold
    }
    candidates = chosen.candidates(signatures)
    found = 0
    verified = 0
    for left, right in candidates:
        agreement = (
            sum(1 for a, b in zip(signatures[left], signatures[right], strict=True) if a == b)
            / width
        )
        if agreement >= threshold:
            verified += 1
            if (left, right) in truth:
                found += 1
    total_pairs = len(names) * (len(names) - 1) // 2
    return Report(
        documents=len(names),
        width=width,
        bands=chosen,
        threshold=threshold,
        true_pairs=len(truth),
        all_pairs=total_pairs,
        candidates=len(candidates),
        found=found,
        missed=len(truth) - found,
        spurious=len(candidates) - verified,
        verified=verified,
    )


def estimate_spread(
    documents: list[tuple[str, str]], *, width: int, shingle_size: int = 5
) -> tuple[float, float, int]:
    """How far the estimate lands from the truth, against what the width promised.

    Each position of the signature agrees with probability `s`, so the estimate has
    variance `s(1-s)/width`: the root mean square error over SIMILAR pairs is
    comparable to `sqrt(s(1-s)/width)` computed from the true similarities. Pairs
    that share nothing are skipped, because both their truth and their estimate are
    zero and averaging them in would report a spread far below the interesting one.
    """
    scheme = MinHash(width, shingle_size=shingle_size)
    sets = {name: shingles(text, shingle_size) for name, text in documents}
    signatures = {name: scheme.signature_of(items) for name, items in sets.items()}
    squared: list[float] = []
    promised: list[float] = []
    for left, right in combinations(sorted(sets), 2):
        exact = jaccard(sets[left], sets[right])
        if exact == 0.0:
            continue
        error = scheme.estimate(signatures[left], signatures[right]) - exact
        squared.append(error * error)
        promised.append(exact * (1.0 - exact) / width)
    if not squared:
        raise ValueError("no pair in this corpus shares a shingle")
    return (
        (sum(squared) / len(squared)) ** 0.5,
        (sum(promised) / len(promised)) ** 0.5,
        len(squared),
    )
