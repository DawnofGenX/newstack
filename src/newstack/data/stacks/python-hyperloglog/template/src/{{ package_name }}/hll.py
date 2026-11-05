"""HyperLogLog: count distinct values from a fixed bag of registers."""

from __future__ import annotations

import math

from .hashing import BITS, hash64

MASK64 = (1 << BITS) - 1
TWO64 = float(1 << BITS)
MIN_PRECISION = 4
MAX_PRECISION = 18
DEFAULT_PRECISION = 14
ALPHA = {16: 0.673, 32: 0.697, 64: 0.709}
SMALL_RANGE_FACTOR = 2.5
LARGE_RANGE_DIVISOR = 30.0


class SketchError(ValueError):
    """A sketch that cannot answer, rather than one that answers wrongly."""


def alpha(m: int) -> float:
    if m == 16:
        return ALPHA[16]
    if m == 32:
        return ALPHA[32]
    if m == 64:
        return ALPHA[64]
    return 0.7213 / (1.0 + 1.079 / m)


def relative_error(precision: int) -> float:
    """The standard error the estimator promises: 1.04 / sqrt(m)."""
    return 1.04 / math.sqrt(1 << precision)


class HyperLogLog:
    """A sketch whose answer is an estimate, and whose estimate carries a promise.

    Two decisions make the promise hold:

    * the register index comes from the TOP bits of the hash and the rank from the
      bits that remain, so the two are independent;
    * the estimator is the harmonic mean of 2**-register, which is dominated by
      the registers that saw the rarest patterns instead of by outliers.
    """

    __slots__ = ("added", "index_mode", "precision", "raised", "registers")

    def __init__(
        self,
        precision: int = DEFAULT_PRECISION,
        registers: bytearray | None = None,
        *,
        index_mode: str = "high",
    ) -> None:
        if not isinstance(precision, int) or isinstance(precision, bool):
            raise SketchError(f"precision must be a whole number, not {precision!r}")
        if not MIN_PRECISION <= precision <= MAX_PRECISION:
            raise SketchError(
                f"precision {precision} is outside {MIN_PRECISION}..{MAX_PRECISION}: "
                "below that the estimate is noise, above it the registers cost more than a set"
            )
        if index_mode not in {"high", "low"}:
            raise SketchError(f"index_mode must be 'high' or 'low', not {index_mode!r}")
        self.precision = precision
        self.index_mode = index_mode
        size = 1 << precision
        if registers is None:
            self.registers = bytearray(size)
        else:
            if len(registers) != size:
                raise SketchError(
                    f"a precision-{precision} sketch needs {size} register(s), not {len(registers)}"
                )
            self.registers = bytearray(registers)
        self.added = 0
        self.raised = 0

    @property
    def size(self) -> int:
        return 1 << self.precision

    @property
    def bytes_used(self) -> int:
        return len(self.registers)

    @property
    def rank_cap(self) -> int:
        return BITS - self.precision + 1

    def _split(self, value: int) -> tuple[int, int]:
        m = self.size
        if self.index_mode == "low":
            index = value & (m - 1)
            rest = value >> self.precision
            rank = (BITS - self.precision) - rest.bit_length() + 1
        else:
            index = value >> (BITS - self.precision)
            rest = value & ((1 << (BITS - self.precision)) - 1)
            rank = (BITS - self.precision) - rest.bit_length() + 1
        return index, min(max(rank, 1), self.rank_cap)

    def add(self, item: str) -> None:
        self.add_hash(hash64(item))

    def add_hash(self, value: int) -> None:
        index, rank = self._split(value)
        self.added += 1
        if rank > self.registers[index]:
            self.registers[index] = rank
            self.raised += 1

    def update(self, items) -> None:
        for item in items:
            self.add(item)

    def zeros(self) -> int:
        return self.registers.count(0)

    def raw_estimate(self) -> float:
        m = self.size
        total = 0.0
        for register in self.registers:
            total += 2.0 ** -register
        return alpha(m) * m * m / total

    def estimate(self) -> float:
        """The raw harmonic estimate, with the two corrections that keep it honest.

        Small cardinalities: too many registers are still zero and the harmonic
        mean is badly biased, so linear counting takes over. Huge cardinalities:
        the estimate approaches 2**64 and the logarithm replaces the arithmetic
        that has run out of float precision.
        """
        m = self.size
        raw = self.raw_estimate()
        zeros = self.zeros()
        if raw <= SMALL_RANGE_FACTOR * m and zeros > 0:
            return m * math.log(m / zeros)
        if raw > TWO64 / LARGE_RANGE_DIVISOR:
            return -TWO64 * math.log(1.0 - raw / TWO64)
        return raw

    def count(self) -> int:
        return round(self.estimate())

    def merged(self, other: HyperLogLog) -> HyperLogLog:
        """Union is register-wise maximum, which is why merging is lossless.

        Summing two estimates would count every item seen by both twice, and
        reinterpreting a different precision's registers would silently move every
        index — both are refused or avoided here rather than approximated.
        """
        if not isinstance(other, HyperLogLog):
            raise SketchError(f"cannot merge a sketch with {type(other).__name__}")
        if other.precision != self.precision:
            raise SketchError(
                f"cannot merge precision {other.precision} into {self.precision}: "
                "the register indexes would be reinterpreted, not combined"
            )
        if other.index_mode != self.index_mode:
            raise SketchError(
                f"cannot merge a {other.index_mode}-index sketch into a {self.index_mode}-index one"
            )
        merged = HyperLogLog(
            self.precision, self.registers, index_mode=self.index_mode
        )
        for index, register in enumerate(other.registers):
            if register > merged.registers[index]:
                merged.registers[index] = register
        merged.added = self.added + other.added
        merged.raised = self.raised + other.raised
        return merged

    def as_dict(self) -> dict:
        return {
            "type": "hyperloglog",
            "precision": self.precision,
            "index_mode": self.index_mode,
            "added": self.added,
            "registers": self.registers.hex(),
        }


def parse_sketch(payload: dict) -> HyperLogLog:
    if not isinstance(payload, dict):
        raise SketchError(f"a sketch is a mapping, not {type(payload).__name__}")
    if payload.get("type") != "hyperloglog":
        raise SketchError(f"{payload.get('type')!r} is not a hyperloglog sketch")
    precision = payload.get("precision")
    if not isinstance(precision, int) or isinstance(precision, bool):
        raise SketchError("a sketch needs a whole-number precision")
    text = payload.get("registers")
    if not isinstance(text, str):
        raise SketchError("a sketch needs its registers as hexadecimal")
    try:
        registers = bytearray.fromhex(text)
    except ValueError as error:
        raise SketchError(f"the registers are not hexadecimal: {error}") from error
    sketch = HyperLogLog(precision, registers, index_mode=payload.get("index_mode", "high"))
    added = payload.get("added", 0)
    if not isinstance(added, int) or isinstance(added, bool) or added < 0:
        raise SketchError("the add count must be a whole number that is not negative")
    sketch.added = added
    return sketch
