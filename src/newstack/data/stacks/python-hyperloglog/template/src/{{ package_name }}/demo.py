"""Six claims about estimation, each one measured before it is printed."""

from __future__ import annotations

from dataclasses import dataclass

from .hashing import hash64, hash64_biased
from .hll import HyperLogLog, relative_error
from .measure import Comparison, compare, kib, set_memory, table_head


@dataclass(frozen=True)
class Story:
    title: str
    lines: tuple[str, ...]
    held: bool

    def render(self) -> list[str]:
        verdict = "holds" if self.held else "BROKEN"
        return [f"{self.title}", *(f"  {line}" for line in self.lines), f"  -> {verdict}", ""]


def items(count: int, prefix: str = "user") -> list[str]:
    return [f"{prefix}:{number}" for number in range(count)]


def hashed(count: int, prefix: str = "user") -> list[int]:
    return [hash64(f"{prefix}:{number}") for number in range(count)]


def count_story() -> Story:
    values = hashed(10_000)
    sketch = HyperLogLog(14)
    for value in values:
        sketch.add_hash(value)
    exact = set(items(10_000))
    comparison = compare(sketch, len(exact))
    return Story(
        "1. an estimate beside the memory it saved",
        (
            f"exact set        {len(exact):>9} distinct, about {kib(set_memory(exact))}",
            f"sketch           {comparison.estimate:>9} distinct, {kib(sketch.bytes_used)}"
            f" (precision {sketch.precision})",
            f"error            {comparison.error * 100:+.2f}%, "
            f"promised {comparison.bound * 100:.2f}%",
            f"registers raised {sketch.raised:>9} of {sketch.added} adds",
        ),
        comparison.within,
    )


def error_story() -> Story:
    lines = [table_head()]
    held = True
    for count in (100, 1_000, 10_000, 100_000):
        values = hashed(count)
        comparison = compare_of(12, values, count)
        held = held and comparison.within
        lines.append(comparison.line())
    return Story(
        "2. the error stays inside the promise for every scale",
        tuple(lines),
        held,
    )


def compare_of(precision: int, values: list[int], n: int) -> Comparison:
    sketch = HyperLogLog(precision)
    for value in values:
        sketch.add_hash(value)
    return compare(sketch, n)


def merge_story() -> Story:
    values = hashed(5_000)
    left = HyperLogLog(12)
    right = HyperLogLog(12)
    for position, value in enumerate(values):
        (left if position % 2 == 0 else right).add_hash(value)
    whole = HyperLogLog(12)
    for value in values:
        whole.add_hash(value)
    merged = left.merged(right)
    same = merged.registers == whole.registers
    return Story(
        "3. merging two halves equals one pass over the whole",
        (
            f"left             {left.count():>9} from {len(values) // 2} adds",
            f"right            {right.count():>9} from {len(values) - len(values) // 2} adds",
            f"merged           {merged.count():>9}",
            f"direct           {whole.count():>9}",
            f"registers equal  {'yes' if same else 'no'}",
            f"estimates added  {left.count() + right.count():>9} (wrong: union is max, not sum)",
        ),
        same and merged.count() == whole.count(),
    )


def duplicate_story() -> Story:
    sketch = HyperLogLog(12)
    for value in hashed(10_000):
        sketch.add_hash(value)
    before = sketch.count()
    raised_before = sketch.raised
    seen = hashed(10_000)
    for _ in range(9):
        for value in seen:
            sketch.add_hash(value)
    after = sketch.count()
    return Story(
        "4. duplicates do not move the estimate",
        (
            f"after 10,000 adds {before:>9}",
            f"after 100,000     {after:>9}",
            f"registers changed {sketch.raised - raised_before:>9}",
            f"adds counted      {sketch.added:>9} (separate from distinct)",
        ),
        before == after,
    )


def bias_story() -> Story:
    precise = HyperLogLog(12)
    biased = HyperLogLog(12, index_mode="low")
    for number in range(10_000):
        text = str(number)
        precise.add_hash(hash64(text))
        biased.add_hash(hash64_biased(text))
    return Story(
        "5. a hash without entropy in the bits you read collapses the sketch",
        (
            f"blake2b 64-bit   {precise.count():>9} for 10,000 distinct numbers",
            f"low 32 bits only {biased.count():>9}",
            f"registers used   {biased.size - biased.zeros():>9} of {biased.size}",
            "the biased hash keeps zeroes in its low bits, so a low-bit index",
            "sends every item to register 0 and the rank is all that is left",
        ),
        precise.count() != biased.count(),
    )


def precision_story() -> Story:
    values = hashed(100_000)
    lines = ["precision  registers  memory   promised  measured"]
    held = True
    for precision in (8, 10, 12, 14, 16):
        comparison = compare_of(precision, values, len(values))
        sketch = HyperLogLog(precision)
        held = held and comparison.within
        lines.append(
            f"{precision:>9}  {sketch.size:>9}  {kib(sketch.bytes_used):>7}  "
            f"{relative_error(precision) * 100:7.2f}%  {comparison.error * 100:+7.2f}%"
        )
    return Story(
        "6. precision buys accuracy and pays in registers",
        tuple(lines),
        held,
    )


def stories() -> list[Story]:
    return [
        count_story(),
        error_story(),
        merge_story(),
        duplicate_story(),
        bias_story(),
        precision_story(),
    ]


def render() -> str:
    lines: list[str] = []
    for story in stories():
        lines.extend(story.render())
    return "\n".join(lines).rstrip() + "\n"
