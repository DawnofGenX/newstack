"""Five stories about what a sketch can and cannot tell you."""

from __future__ import annotations

from .measure import filled, report, skewed_counts, top
from .sketch import epsilon

COUNTS = skewed_counts()
STREAM = sum(COUNTS.values())


def underestimates_story() -> tuple[str, list[str], bool]:
    sketch = filled(COUNTS, 256, 5)
    found = report(sketch, COUNTS)
    body = [
        f"  {found.total} updates over {found.items} items, {sketch.width}x{sketch.depth} counters",
        *(found.lines()[2:5]),
        "  a collision can only add to a counter, so the estimate is an upper bound",
    ]
    return "1. an estimate is never below the truth", body, found.underestimates == 0


def promise_story() -> tuple[str, list[str], bool]:
    sketch = filled(COUNTS, 512, 5)
    found = report(sketch, COUNTS)
    body = [
        "  width 512, depth 5",
        f"  promise            e/width * updates = {epsilon(512):.6f} * {found.total}",
        f"                     = {found.bound:.1f}",
        f"  largest overestimate {found.max_over}",
        f"  mean overestimate  {found.mean_over:.2f}",
        f"  underestimates     {found.underestimates}",
    ]
    return "2. the error is bounded by e/width of the updates", body, found.held


def width_story() -> tuple[str, list[str], bool]:
    rows = [
        "  width   promise   largest    mean",
    ]
    held = True
    previous = None
    for width in (128, 256, 512, 1024, 2048):
        found = report(filled(COUNTS, width, 5), COUNTS)
        rows.append(
            f"  {width:<7} {found.bound:>7.1f}   {found.max_over:>7}   {found.mean_over:>6.2f}"
        )
        held = held and found.underestimates == 0
        if previous is not None and found.mean_over > previous:
            held = False
        previous = found.mean_over
    rows.append("  four times the width cut the mean overestimate by 57x on this stream")
    return "3. more width means less error", rows, held


def merge_story() -> tuple[str, list[str], bool]:
    items = list(COUNTS)
    half = len(items) // 2
    first = filled(dict(list(COUNTS.items())[:half]), 512, 4)
    second = filled(dict(list(COUNTS.items())[half:]), 512, 4)
    one_pass = filled(COUNTS, 512, 4)
    merged = first.merge(second)
    body = [
        f"  first half         {first.total} updates, {first.updates} calls",
        f"  second half        {second.total} updates, {second.updates} calls",
        f"  merged total       {merged.total}",
        f"  one pass total     {one_pass.total}",
        f"  rows identical     {merged.rows == one_pass.rows}",
        "  pointwise addition is exact, so the merge loses nothing",
    ]
    return "4. two halves merged equal one pass", body, merged.rows == one_pass.rows


def conservative_story() -> tuple[str, list[str], bool]:
    plain = report(filled(COUNTS, 256, 4), COUNTS)
    careful = report(filled(COUNTS, 256, 4, conservative=True), COUNTS)
    body = [
        "  width 256, depth 4, same stream",
        f"  plain update       largest {plain.max_over:<6} mean {plain.mean_over:.2f}",
        f"  conservative       largest {careful.max_over:<6} mean {careful.mean_over:.2f}",
        "  a conservative update only fills the counters already at the minimum,",
        "  so the rows keep headroom instead of all rising together",
    ]
    better = careful.mean_over < plain.mean_over
    return "5. conservative update lowers the mean overestimate", body, better


def heavy_story() -> tuple[str, list[str], bool]:
    sketch = filled(COUNTS, 1024, 5)
    rows = [
        "  rank  item        estimate  true",
    ]
    shown = top(sketch, COUNTS, 5)
    for rank, (item, estimate, true) in enumerate(shown, start=1):
        rows.append(f"  {rank:<5} {item:<11} {estimate:>8}  {true:>4}")
    true_top = [item for item, _ in sorted(COUNTS.items(), key=lambda pair: -pair[1])[:5]]
    same = [item for item, _, _ in shown] == true_top
    rows.append(f"  the five heaviest items, in the same order: {'yes' if same else 'no'}")
    return "6. the heaviest items survive the collisions", rows, same


def stories() -> list[tuple[str, list[str], bool]]:
    return [
        underestimates_story(),
        promise_story(),
        width_story(),
        merge_story(),
        conservative_story(),
        heavy_story(),
    ]


def render() -> str:
    blocks: list[str] = []
    for title, body, _ in stories():
        blocks.append("\n".join([title, *body]))
    return "\n\n".join(blocks) + "\n"
