"""Six stories about similarity, each of which either holds or prints BROKEN."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .corpus import document, family, pair
from .lsh import Bands, pick
from .measure import estimate_spread, evaluate
from .minhash import MinHash
from .shingles import jaccard, shingles

CORPUS_DOCUMENTS = 200
CORPUS_DUPLICATES = 120
REPLACE_EVERY = 40
THRESHOLD = 0.8


@dataclass(frozen=True)
class Story:
    title: str
    lines: list[str]
    held: bool


def _pair_story() -> Story:
    base, edited, name = pair(replace_every=20, words=200)
    exact = jaccard(shingles(base), shingles(edited))
    lines = [f"pair         {name}, two documents whose exact jaccard is {exact:.4f}"]
    held = True
    for width in (32, 128, 512, 2048):
        scheme = MinHash(width)
        estimate = scheme.estimate(scheme.signature(base), scheme.signature(edited))
        held = held and abs(estimate - exact) <= 3.0 * scheme.error
        lines.append(
            f"width {width:>5}   estimate {estimate:.4f}, promised deviation {scheme.error:.4f}"
        )
    lines.append("the estimate is one draw from that error, not the similarity itself")
    return Story("1. a signature estimates the similarity, it does not measure it", lines, held)


def _shingle_story() -> Story:
    base = document(21, words=120)
    noisy = "  ".join(re.split(r"\s+", base.upper())) + "!!"
    plain, noisy_set = shingles(base), shingles(noisy)
    scheme = MinHash(128)
    same = scheme.signature(base) == scheme.signature(noisy)
    lines = [
        f"exact        jaccard {jaccard(plain, noisy_set):.4f} after upper-casing, "
        "doubling the spaces and adding punctuation",
        f"same set     {len(plain)} shingle(s) each, identical: {plain == noisy_set}",
        f"same stamp   the 128-position signatures agree: {same}",
        "at shingle size 1 the same two phrases are different documents: "
        f"{shingles('cat', 1) != shingles('the cat', 1)}",
        "the shingle size is the definition of similar; the hash only speeds it up",
    ]
    return Story(
        "2. the shingle set is the definition, so whitespace does not count",
        lines,
        jaccard(plain, noisy_set) == 1.0 and same,
    )


def _curve_story() -> Story:
    chosen = pick(128, THRESHOLD)
    shapes = (Bands(4, 32), chosen, Bands(32, 4))
    header = "similarity  " + "  ".join(f"{shape.bands}x{shape.rows}".rjust(9) for shape in shapes)
    lines = [
        f"chosen       {chosen.describe()} for a {THRESHOLD:.2f} threshold, "
        f"whose half-way similarity is {chosen.threshold():.3f}",
        header,
    ]
    for similarity in (0.4, 0.6, 0.7, 0.8, 0.9):
        row = f"{similarity:>10.2f}  " + "  ".join(
            f"{shape.probability(similarity):>9.3f}" for shape in shapes
        )
        lines.append(row)
    lines.append("a banding is a decision about which false negatives you accept")
    return Story(
        "3. banding turns a signature into a threshold you chose",
        lines,
        chosen.probability(0.95) > 0.99 and chosen.probability(0.6) < 0.01,
    )


def _corpus() -> list[tuple[str, str]]:
    return family(count=CORPUS_DOCUMENTS, duplicates=CORPUS_DUPLICATES, replace_every=REPLACE_EVERY)


def _candidate_story() -> Story:
    documents = _corpus()
    bands = pick(128, THRESHOLD)
    report = evaluate(documents, width=128, bands=bands, threshold=THRESHOLD)
    lines = [
        f"documents    {len(documents)}, which is {report.all_pairs:,} pairs to compare",
        f"banding      {bands.describe()}",
        f"candidates   {report.candidates:,} pair(s), so {report.reduction:.1%} of the pairs are "
        "never compared",
        f"exact        {report.true_pairs:,} pair(s) at or above {THRESHOLD:.2f}",
        f"found        {report.found:,} of {report.true_pairs:,}, so {report.missed:,} "
        "duplicate(s) never became a candidate at this banding",
        f"refused      {report.spurious} candidate(s) were rejected by the estimate, "
        "which is why a verified candidate is a decision and not a guess",
        "the filter is allowed to be wrong in one direction: a missing candidate is a missed "
        "duplicate",
    ]
    return Story(
        "4. candidates are a fraction of the pairs, and they are verified",
        lines,
        report.candidates < report.all_pairs / 10,
    )


def _recall_story() -> Story:
    documents = _corpus()
    lines = ["banding        predicted   measured   missed"]
    held = True
    shapes = (Bands(32, 4), Bands(16, 8), Bands(8, 16), Bands(4, 32))
    for shape in shapes:
        report = evaluate(documents, width=128, bands=shape, threshold=THRESHOLD)
        predicted = shape.probability(0.854)
        lines.append(
            f"{shape.describe():<32} {predicted:>7.3f}   {report.recall:>8.3f}   {report.missed:>6}"
        )
        held = held and abs(predicted - report.recall) <= 0.06
    lines.append(
        "the measured recall tracks the curve, which is why the curve can be printed "
        "before the data"
    )
    return Story("5. the recall you get is the curve you chose", lines, held)


def _width_story() -> Story:
    documents = _corpus()
    lines = ["width    rmse of the estimate   sqrt(s(1-s)/width)   pairs"]
    held = True
    for width in (128, 512, 2048):
        measured, promised, pairs = estimate_spread(documents, width=width)
        lines.append(f"{width:>5}    {measured:>19.4f}   {promised:>18.4f}   {pairs:>5}")
        held = held and abs(measured - promised) <= 0.5 * promised
    lines.append(
        "a wider signature does not change the banding; it changes how much the estimate is worth"
    )
    return Story("6. width buys certainty about the estimate, not recall", lines, held)


def stories() -> list[Story]:
    return [
        _pair_story(),
        _shingle_story(),
        _curve_story(),
        _candidate_story(),
        _recall_story(),
        _width_story(),
    ]


def render_stories() -> tuple[list[str], bool]:
    rows: list[str] = []
    every = True
    for story in stories():
        rows.append(story.title)
        rows.extend(f"  {line}" for line in story.lines)
        rows.append("  -> holds" if story.held else "  -> BROKEN")
        rows.append("")
        every = every and story.held
    return rows, every


def main() -> int:
    rows, held = render_stories()
    print("\n".join(rows).rstrip())
    return 0 if held else 1
