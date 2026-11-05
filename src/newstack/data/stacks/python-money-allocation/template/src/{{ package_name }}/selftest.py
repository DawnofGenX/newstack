"""The built-in checks: every claim the README makes, with its proof in the same file."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from . import allocation, parse
from .errors import AllocationError, CurrencyMismatch, ParseError, UnknownCurrency
from .model import CURRENCIES, Money, currency_of


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool) -> None:
        if condition:
            self.passed += 1
            print(f"ok   {name}")
        else:
            self.failed += 1
            print(f"FAIL {name}")

    def equal(self, name: str, want: object, got: object) -> None:
        self.ok(f"{name} (want {want!r}, got {got!r})", want == got)

    def raises(self, name: str, error: type[BaseException], action: Callable[[], object]) -> None:
        try:
            action()
        except error:
            self.ok(name, True)
        except BaseException as unexpected:
            self.ok(f"{name} (raised {type(unexpected).__name__} instead)", False)
        else:
            self.ok(f"{name} (nothing was raised)", False)


def _currency_checks(checks: Checks) -> None:
    checks.equal("USD has two decimals", 100, currency_of("USD").scale)
    checks.equal("JPY has none", 1, currency_of("JPY").scale)
    checks.equal("KWD has three", 1000, currency_of("KWD").scale)
    checks.equal("lower case is accepted", "USD", currency_of("usd").code)
    checks.equal("the table is what it says", 6, len(CURRENCIES))
    checks.raises("an unknown code is refused", UnknownCurrency, lambda: Money(1, "XYZ"))
    checks.raises("a float amount is refused", TypeError, lambda: Money(1.0, "USD"))
    checks.raises("a bool amount is refused", TypeError, lambda: Money(True, "USD"))


def _arithmetic_checks(checks: Checks) -> None:
    ten = Money(1000, "USD")
    five = Money(500, "USD")
    checks.equal("addition is exact", 1500, ten.add(five).amount)
    checks.equal("subtraction is exact", 500, ten.subtract(five).amount)
    checks.equal("negation is exact", -1000, ten.negate().amount)
    checks.equal("a whole multiplier is exact", 3000, ten.times(3).amount)
    checks.equal("a decimal multiplier rounds once", 333, ten.times(Decimal("0.3333")).amount)
    checks.equal("a percentage rounds once", 180, ten.percent(Decimal(18)).amount)
    checks.equal("compare answers -1", -1, five.compare(ten))
    checks.equal("compare answers 0", 0, ten.compare(Money(1000, "USD")))
    checks.raises("a float multiplier is refused", TypeError, lambda: ten.times(0.5))
    checks.raises(
        "adding another currency is refused",
        CurrencyMismatch,
        lambda: ten.add(Money(500, "INR")),
    )
    checks.raises(
        "comparing another currency is refused",
        CurrencyMismatch,
        lambda: ten.compare(Money(500, "INR")),
    )


def _format_checks(checks: Checks) -> None:
    cases = (
        ("two decimals are printed", "12.34 USD", Money(1234, "USD")),
        ("a zero-padded minor unit is printed", "12.05 USD", Money(1205, "USD")),
        ("thousands are grouped", "1,234,567.89 USD", Money(123456789, "USD")),
        ("a negative keeps its sign", "-12.34 USD", Money(-1234, "USD")),
        ("JPY has no decimal point", "1,200 JPY", Money(1200, "JPY")),
        ("KWD keeps three places", "1.234 KWD", Money(1234, "KWD")),
        ("a small negative keeps its zero", "-0.05 USD", Money(-5, "USD")),
    )
    for name, want, money in cases:
        checks.equal(name, want, money.format())
    checks.equal("major units are a Decimal", Decimal("12.34"), Money(1234, "USD").major())


def _parse_checks(checks: Checks) -> None:
    def holds(name: str, text: str, amount: int, rounding: str | None = None) -> None:
        checks.equal(name, amount, parse.parse(text, rounding).amount)

    def refuses(name: str, text: str, rounding: str | None = None) -> None:
        checks.raises(name, ParseError, lambda: parse.parse(text, rounding))

    holds("an amount and a code parse", "12.34 USD", 1234)
    holds("the code may come first", "USD 12.34", 1234)
    holds("thousands separators are accepted", "1,234,567.89 USD", 123456789)
    holds("JPY takes a whole number", "1200 JPY", 1200)
    holds("a negative parses", "-12.34 USD", -1234)
    holds("a named rounding mode is applied", "12.344 USD", 1234, "half-even")
    holds("half-up rounds a tie away from zero", "12.345 USD", 1235, "half-up")
    holds("half-even rounds a tie to the even digit", "12.345 USD", 1234, "half-even")
    holds("a tie one unit higher rounds away", "12.355 USD", 1236, "half-even")
    holds("down truncates", "12.349 USD", 1234, "down")
    holds("up rounds away from zero", "12.341 USD", 1235, "up")
    holds("JPY refuses a fraction", "1200.5 JPY", 1201, "half-up")
    refuses("a third decimal place is refused", "12.345 USD")
    refuses("JPY refuses a fraction by default", "1200.5 JPY")
    refuses("a decimal comma is refused, not read as thousands", "12,34 USD")
    refuses("an unknown code is refused", "12.34 XYZ")
    refuses("one token is not enough", "12.34")
    refuses("empty text is refused", "")
    refuses("an unknown rounding is refused", "1 USD", "sideways")


def _allocation_checks(checks: Checks) -> None:
    def shares(name: str, ratios: list[int], want: list[int], amount: int = 10000) -> None:
        got = [part.amount for part in allocation.allocate(Money(amount, "USD"), ratios)]
        checks.equal(name, want, got)

    def impossible(name: str, ratios: list[int]) -> None:
        action = lambda: allocation.allocate(Money(100, "USD"), ratios)  # noqa: E731
        checks.raises(name, AllocationError, action)

    shares("an even split of 100.00", [1, 1, 1], [3334, 3333, 3333])
    shares("the largest remainder takes the extra unit", [3, 2, 1], [5000, 3333, 1667])
    shares("a single ratio gets everything", [7], [10000])
    shares("zero ratios still balance", [1, 0], [10000, 0])
    shares("a negative amount splits too", [1, 1, 1], [-334, -333, -333], amount=-1000)
    shares("a three-way split of 1 JPY", [1, 1, 1], [1, 0, 0], amount=1)

    parts = allocation.allocate(Money(10000, "USD"), [1, 1, 1])
    checks.equal("and the parts add back up", 10000, sum(part.amount for part in parts))
    negative = allocation.allocate(Money(-1000, "USD"), [1, 1, 1])
    checks.equal("a negative split balances too", -1000, sum(p.amount for p in negative))

    impossible("an empty ratio list is refused", [])
    impossible("all-zero ratios are refused", [0, 0])
    impossible("a negative ratio is refused", [1, -1])
    impossible("a float ratio is refused", [1.0])
    checks.raises(
        "zero parts is refused",
        AllocationError,
        lambda: allocation.split(Money(100, "USD"), 0),
    )

    big = Money(10**18 + 1, "USD")
    huge = allocation.allocate(big, [3, 3, 4])
    checks.equal("a huge amount still balances", big.amount, sum(p.amount for p in huge))
    checks.ok("and every share is an integer", all(isinstance(p.amount, int) for p in huge))


def run() -> int:
    checks = Checks()
    groups = (
        _currency_checks,
        _arithmetic_checks,
        _format_checks,
        _parse_checks,
        _allocation_checks,
    )
    for group in groups:
        group(checks)
    total = checks.passed + checks.failed
    print(f"\nselftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
