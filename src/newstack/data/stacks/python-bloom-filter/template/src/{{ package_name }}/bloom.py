"""Bit-array membership with hashes derived from one digest (Kirsch-Mitzenmacher)."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

LN2 = math.log(2)
SATURATION = 255

# At this fill the answer is "yes" for most lookups, whatever k was chosen.
SATURATED_FILL = 0.9


class BloomFilterError(ValueError):
    """Raised when the stored filter or its parameters cannot be used as given."""


def _require_count(value: object, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise BloomFilterError(f"{what} {value!r} is not an integer")
    if value < 1:
        raise BloomFilterError(f"{what} {value!r} must be at least 1")
    return value


@dataclass(frozen=True)
class Sizing:
    """The shape a filter needs to hold ``expected`` items near ``fp_rate``."""

    m_bits: int
    k_hashes: int
    expected: int
    fp_rate: float

    @property
    def bits_per_item(self) -> float:
        return self.m_bits / self.expected

    @property
    def predicted_rate(self) -> float:
        """The textbook rate, ``(1 - e^(-kn/m))^k``, at exactly full capacity."""
        return (1 - math.exp(-self.k_hashes * self.expected / self.m_bits)) ** self.k_hashes

    def lines(self) -> list[str]:
        return [
            f"expected    {self.expected} item(s)",
            f"target rate {self.fp_rate:.6f}",
            f"bits        {self.m_bits} ({self.bits_per_item:.2f} per item)",
            f"hashes      {self.k_hashes}",
            f"predicted   {self.predicted_rate:.6f} at full capacity",
        ]


def sized_for(expected: int, fp_rate: float) -> Sizing:
    """The smallest bit array that holds ``expected`` items at roughly ``fp_rate``."""
    _require_count(expected, "expected item count")
    if isinstance(fp_rate, bool) or not isinstance(fp_rate, (int, float)):
        raise BloomFilterError(f"false-positive rate {fp_rate!r} is not a number")
    if not 0 < fp_rate < 1:
        raise BloomFilterError(f"false-positive rate {fp_rate!r} must be between 0 and 1")
    m_bits = math.ceil(-expected * math.log(fp_rate) / (LN2**2))
    k_hashes = max(1, round(m_bits / expected * LN2))
    return Sizing(m_bits, k_hashes, expected, float(fp_rate))


class Hashed:
    """The hashing half, shared by the plain and the counting filter."""

    type_name = "base"

    def __init__(self, m_bits: int, k_hashes: int) -> None:
        self._m = _require_count(m_bits, "bit count")
        self._k = _require_count(k_hashes, "hash count")

    @property
    def m_bits(self) -> int:
        return self._m

    @property
    def k_hashes(self) -> int:
        return self._k

    def digest(self, item: str) -> bytes:
        return hashlib.blake2b(item.encode("utf-8"), digest_size=16, person=b"bloom").digest()

    def positions(self, item: str) -> tuple[int, ...]:
        """One digest, two halves, k positions: h_i = h1 + i * h2 (mod m)."""
        digest = self.digest(item)
        first = int.from_bytes(digest[:8], "big")
        second = int.from_bytes(digest[8:], "big") | 1
        return tuple((first + step * second) % self._m for step in range(self._k))


class Bloom(Hashed):
    """A bit array. It can answer "definitely absent" and nothing stronger."""

    type_name = "bloom"

    def __init__(self, m_bits: int, k_hashes: int, bits: bytes | None = None) -> None:
        super().__init__(m_bits, k_hashes)
        size = (self._m + 7) // 8
        if bits is None:
            self._bits = bytearray(size)
        else:
            if len(bits) != size:
                raise BloomFilterError(
                    f"the stored filter holds {len(bits)} byte(s) but {self._m} bits "
                    f"need {size}"
                )
            self._bits = bytearray(bits)

    def add(self, item: str) -> tuple[int, ...]:
        """Set the item's bits; return only the positions that were not already set."""
        fresh = []
        for pos in self.positions(item):
            index, offset = divmod(pos, 8)
            if not self._bits[index] & (1 << offset):
                self._bits[index] |= 1 << offset
                fresh.append(pos)
        return tuple(fresh)

    def might_contain(self, item: str) -> bool:
        return all(
            self._bits[pos >> 3] & (1 << (pos & 7)) for pos in self.positions(item)
        )

    def clear(self, item: str) -> tuple[int, ...]:
        """The wrong way to remove: it also erases whatever else shares those bits."""
        cleared = []
        for pos in self.positions(item):
            index, offset = divmod(pos, 8)
            if self._bits[index] & (1 << offset):
                self._bits[index] &= ~(1 << offset) & 0xFF
                cleared.append(pos)
        return tuple(cleared)

    def bits_set(self) -> int:
        count = 0
        tail = self._m % 8
        last = len(self._bits) - 1
        for index, byte in enumerate(self._bits):
            if tail and index == last:
                byte &= (1 << tail) - 1
            count += bin(byte).count("1")
        return count

    def fill(self) -> float:
        return self.bits_set() / self._m

    def predict_rate(self) -> float:
        """With k independent-looking bits, a random absent item passes at fill ** k."""
        return self.fill() ** self._k

    def estimate_items(self) -> float | None:
        """Invert the fill formula; None means the fill is too high to invert."""
        fill = self.fill()
        if fill <= 0:
            return 0.0
        if fill >= 1:
            return None
        return -(self._m / self._k) * math.log(1 - fill)

    def is_saturated(self) -> bool:
        """A filter at its design capacity sits near fill 0.5; 0.9 is past any use."""
        return self.fill() >= SATURATED_FILL

    def as_dict(self) -> dict[str, object]:
        return {
            "type": self.type_name,
            "m_bits": self._m,
            "k_hashes": self._k,
            "bits": bytes(self._bits).hex(),
        }


class CountingBloom(Hashed):
    """One saturating byte counter per bit: the only way a removal can be safe."""

    type_name = "counting-bloom"

    def __init__(self, m_bits: int, k_hashes: int, counters: bytes | None = None) -> None:
        super().__init__(m_bits, k_hashes)
        if counters is None:
            self._counters = bytearray(self._m)
        else:
            if len(counters) != self._m:
                raise BloomFilterError(
                    f"the stored filter holds {len(counters)} counter(s) but {self._m} "
                    "positions need one each"
                )
            self._counters = bytearray(counters)

    def add(self, item: str) -> tuple[int, ...]:
        """Increment each counter, stopping at 255; return the positions that saturated."""
        saturated = []
        for pos in self.positions(item):
            if self._counters[pos] < SATURATION:
                self._counters[pos] += 1
            if self._counters[pos] == SATURATION:
                saturated.append(pos)
        return tuple(saturated)

    def remove(self, item: str) -> tuple[int, ...]:
        """Decrement the counters, refusing an item that was never added here."""
        if not self.might_contain(item):
            raise BloomFilterError(
                f"cannot remove {item!r}: at least one counter is already zero, so this "
                "filter has no record of the add"
            )
        for pos in self.positions(item):
            self._counters[pos] -= 1
        return self.positions(item)

    def might_contain(self, item: str) -> bool:
        return all(self._counters[pos] > 0 for pos in self.positions(item))

    def bits_set(self) -> int:
        return sum(1 for counter in self._counters if counter > 0)

    def saturated_positions(self) -> int:
        return sum(1 for counter in self._counters if counter == SATURATION)

    def fill(self) -> float:
        return self.bits_set() / self._m

    def predict_rate(self) -> float:
        return self.fill() ** self._k

    def estimate_items(self) -> float | None:
        fill = self.fill()
        if fill <= 0:
            return 0.0
        if fill >= 1:
            return None
        return -(self._m / self._k) * math.log(1 - fill)

    def is_saturated(self) -> bool:
        return self.fill() >= SATURATED_FILL

    def as_dict(self) -> dict[str, object]:
        return {
            "type": self.type_name,
            "m_bits": self._m,
            "k_hashes": self._k,
            "counters": bytes(self._counters).hex(),
        }


FILTERS = {Bloom.type_name: Bloom, CountingBloom.type_name: CountingBloom}


def parse_filter(payload: object) -> Bloom | CountingBloom:
    if not isinstance(payload, dict):
        raise BloomFilterError("a stored filter is a JSON object")
    kind = payload.get("type")
    if kind not in FILTERS:
        raise BloomFilterError(
            f"unknown filter type {kind!r}; this build knows {sorted(FILTERS)}"
        )
    try:
        m_bits = payload["m_bits"]
        k_hashes = payload["k_hashes"]
    except KeyError as error:
        raise BloomFilterError(f"the stored filter has no {error.args[0]}") from None
    if kind == Bloom.type_name:
        stored = payload.get("bits")
        if not isinstance(stored, str):
            raise BloomFilterError("the stored filter has no bit array")
        try:
            return Bloom(m_bits, k_hashes, bytes.fromhex(stored))
        except BloomFilterError:
            raise
        except ValueError as error:
            raise BloomFilterError(f"the bit array is not hexadecimal: {error}") from None
    stored = payload.get("counters")
    if not isinstance(stored, str):
        raise BloomFilterError("the stored counting filter has no counter array")
    try:
        return CountingBloom(m_bits, k_hashes, bytes.fromhex(stored))
    except ValueError as error:
        raise BloomFilterError(f"the counters are not hexadecimal: {error}") from None
