"""Turning text into minor units, with the rounding decision made visible.

`Decimal("12.345")` is not an amount in USD: USD has two decimal places, and the third one is
a decision, not a digit. By default this parser refuses the ambiguity; a caller who wants a
rounding policy has to name it.
"""

from __future__ import annotations

import re
from decimal import Decimal

from .errors import ParseError
from .model import CURRENCIES, Currency, Money, currency_of

AMOUNT = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?$")
# A comma is a thousands separator only when it groups exactly three digits. Blanket-stripping
# commas turns the European "12,34" into 1234, which is a silent 100x error.
GROUPED = re.compile(r"^-?[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?$")
ROUNDINGS = {
    "half-even": "ROUND_HALF_EVEN",
    "half-up": "ROUND_HALF_UP",
    "down": "ROUND_DOWN",
    "up": "ROUND_UP",
}


def to_minor(value: Decimal, currency: Currency, rounding: str | None = None) -> int:
    """Convert a major-unit Decimal to minor units, refusing a fraction nobody chose."""
    scaled = value.scaleb(currency.exponent)
    if scaled == scaled.to_integral_value():
        return int(scaled)
    if rounding is None:
        places = "no decimal places" if currency.exponent == 0 else f"{currency.exponent}"
        raise ParseError(
            f"{value} has more decimal places than {currency.code} allows ({places}); "
            f"pass a rounding mode ({', '.join(sorted(ROUNDINGS))}) to choose the loss"
        )
    return int(scaled.quantize(Decimal(1), rounding=ROUNDINGS[rounding]))


def split_amount(text: str) -> tuple[Decimal, str]:
    """Split `12.34 USD` or `USD 12.34` into an amount and a code."""
    tokens = text.split()
    if len(tokens) != 2:
        raise ParseError(f"{text!r} is not an amount and a currency code, e.g. '12.34 USD'")
    first, second = tokens
    if first.upper() in CURRENCIES and second.upper() not in CURRENCIES:
        amount_text, code = second, first.upper()
    elif second.upper() in CURRENCIES:
        amount_text, code = first, second.upper()
    else:
        known = ", ".join(sorted(CURRENCIES))
        raise ParseError(f"no known currency code in {text!r}; known currencies are {known}")
    if "," in amount_text and not GROUPED.match(amount_text):
        raise ParseError(
            f"{amount_text!r} uses a comma that is not a thousands separator; "
            "write the decimal point as '.' and group digits in threes"
        )
    cleaned = amount_text.replace(",", "")
    if not AMOUNT.match(cleaned):
        raise ParseError(f"{amount_text!r} is not a decimal amount")
    return Decimal(cleaned), code


def parse(text: str, rounding: str | None = None) -> Money:
    """Parse `'12.34 USD'` into `Money(1234, 'USD')`."""
    if rounding is not None and rounding not in ROUNDINGS:
        raise ParseError(f"unknown rounding {rounding!r}; expected one of {', '.join(ROUNDINGS)}")
    amount, code = split_amount(text.strip())
    currency = currency_of(code)
    return Money(to_minor(amount, currency, rounding), currency.code)
