"""Currency and Money: an integer number of minor units, and nothing else.

The whole file exists to keep one promise: money is never a float, and the currency travels
with the amount so it cannot be added to the wrong one.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .errors import CurrencyMismatch, UnknownCurrency


@dataclass(frozen=True, slots=True)
class Currency:
    """A currency is a code and the number of decimal places the code actually uses."""

    code: str
    exponent: int

    def __post_init__(self) -> None:
        if self.exponent < 0:
            raise ValueError("exponent cannot be negative")

    @property
    def scale(self) -> int:
        return 10**self.exponent


# The table is the source of truth: JPY has no minor unit, KWD has three. Getting this from
# a locale or an ICU database is a dependency; getting it wrong is a 100x error.
CURRENCIES: dict[str, Currency] = {
    "USD": Currency("USD", 2),
    "EUR": Currency("EUR", 2),
    "GBP": Currency("GBP", 2),
    "INR": Currency("INR", 2),
    "JPY": Currency("JPY", 0),
    "KWD": Currency("KWD", 3),
}


def currency_of(code: str) -> Currency:
    """Look a code up, refusing loudly instead of assuming two decimal places."""
    try:
        return CURRENCIES[code.upper()]
    except KeyError:
        known = ", ".join(sorted(CURRENCIES))
        raise UnknownCurrency(f"unknown currency {code!r}; known currencies are {known}") from None


@dataclass(frozen=True, slots=True)
class Money:
    """An amount in minor units and the currency it belongs to.

    There is deliberately no `order=True`: a tuple comparison would happily say 5 JPY < 5 USD,
    so ordering goes through `compare()`, which refuses a mismatch like the arithmetic does.
    """

    amount: int
    currency: str

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError(f"amount must be an integer number of minor units, got {self.amount!r}")
        object.__setattr__(self, "currency", self.currency.upper())
        currency_of(self.currency)

    # --- arithmetic -------------------------------------------------------------------

    def add(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def negate(self) -> Money:
        return Money(-self.amount, self.currency)

    def percent(self, rate: Decimal) -> Money:
        """Apply a percentage (18 for 18%) with the default half-to-even rounding."""
        if not isinstance(rate, Decimal):
            raise TypeError("percent() takes a Decimal; percentage points are not floats")
        return Money(round_decimal(Decimal(self.amount) * rate / Decimal(100)), self.currency)

    def times(self, factor: int | Decimal) -> Money:
        """Multiply by a whole number exactly, or by a Decimal with the caller's rounding."""
        if isinstance(factor, int) and not isinstance(factor, bool):
            return Money(self.amount * factor, self.currency)
        if not isinstance(factor, Decimal):
            raise TypeError("times() takes an int or a Decimal; a float is how cents appear")
        return Money(round_decimal(Decimal(self.amount) * factor), self.currency)

    # --- comparison -------------------------------------------------------------------

    def _check(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(self.currency, other.currency)

    def compare(self, other: Money) -> int:
        """Return -1, 0 or 1, refusing to answer across currencies."""
        self._check(other)
        return (self.amount > other.amount) - (self.amount < other.amount)

    def is_zero(self) -> bool:
        return self.amount == 0

    def __str__(self) -> str:
        return self.format()

    def format(self, symbol: str = "") -> str:
        currency = currency_of(self.currency)
        sign = "-" if self.amount < 0 else ""
        units = abs(self.amount)
        major, minor = divmod(units, currency.scale)
        if currency.exponent == 0:
            body = f"{major:,}"
        else:
            body = f"{major:,}.{minor:0{currency.exponent}d}"
        return f"{sign}{symbol}{body} {self.currency}"

    def major(self) -> Decimal:
        """The amount as a Decimal in major units — for display, never for arithmetic."""
        return Decimal(self.amount).scaleb(-currency_of(self.currency).exponent)


def round_decimal(value: Decimal) -> int:
    """Round a Decimal to an integer with the default policy: half to even.

    This is the function every other conversion funnels through, so there is exactly one
    place where a fraction of a minor unit disappears.
    """
    return int(value.quantize(Decimal(1), rounding="ROUND_HALF_EVEN"))
