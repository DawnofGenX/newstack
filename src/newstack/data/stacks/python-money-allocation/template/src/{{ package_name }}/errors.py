"""One exception family, so a caller can catch `MoneyError` and mean it."""

from __future__ import annotations


class MoneyError(ValueError):
    """Base class: every refusal in this package is a `ValueError` a caller can catch."""


class UnknownCurrency(MoneyError):
    """The code is not in the table. Guessing an exponent is how 100 JPY become 10000."""


class CurrencyMismatch(MoneyError):
    """Adding dollars to rupees is not arithmetic, it is a bug with a rounding error attached."""

    def __init__(self, left: str, right: str) -> None:
        super().__init__(f"cannot combine {left} with {right}")
        self.left = left
        self.right = right


class ParseError(MoneyError):
    """The text is not an amount in a currency this package knows."""


class AllocationError(MoneyError):
    """The split cannot be made exact, or the ratios are not ratios."""
