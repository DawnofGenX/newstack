# {{ title }}

{{ description }}

Money is an integer count of minor units plus the currency code it belongs to: `100.00 USD` is
`Money(10000, "USD")`. There is no float anywhere in the library, so there is no place for a
cent to go missing.

    uv venv --allow-existing .venv
    uv pip install --python .venv/bin/python -e . pytest ruff
    .venv/bin/python -m {{ package_name }} parse '12.34 USD'

```
minor     1234  exponent 2  12.34 USD
```

The minor units are printed next to the formatted amount on purpose: the number a database
stores and the number a human reads should be visible at the same time.

## Allocating

```
$ .venv/bin/python -m {{ package_name }} alloc '100.00 USD' 3 2 1
share 0  ratio    3  50.00 USD
share 1  ratio    2  33.33 USD
share 2  ratio    1  16.67 USD
total       100.00 USD  (wanted 100.00 USD)
balances    yes
```

```
$ .venv/bin/python -m {{ package_name }} split '0.10 USD' 3
share 0  0.04 USD
share 1  0.03 USD
share 2  0.03 USD
```

`0.10 / 3` is not `0.033333`; it is three shares that add up to `0.10`, with the leftover minor
unit going somewhere explicit — here to the first share. Every allocation either balances or
raises `AllocationError("allocation did not balance; this is a bug, not a rounding error")`.

## Refusals

```
$ .venv/bin/python -m {{ package_name }} parse '12.345 USD'
{{ npm_name }}: 12.345 has more decimal places than USD allows (2); pass a rounding mode (down, half-even, half-up, up) to choose the loss
```

```
$ .venv/bin/python -m {{ package_name }} parse '12.345 USD' --round half-up
minor     1235  exponent 2  12.35 USD
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the command did what it says |
| 2 | the input was not usable: bad amount, unknown currency, impossible ratios |

## The traps this stack encodes

1. **A float is not money.** `0.1 + 0.2` is `0.30000000000000004`. Every cent that disappears
   from a billing system starts with a float, so `Money` refuses one: `Money(12.5, "USD")` and
   `money.times(0.5)` both raise `TypeError`.
2. **The exponent is not always 2.** JPY has 0, KWD has 3. A currency code without its exponent
   is half a type, so `Currency` carries both and `Money` validates the code it is given.
3. **Rounding is a decision, so it needs a name.** `parse('12.345 USD')` raises rather than
   picking a policy; `--round half-even|half-up|down|up` is how you choose the loss.
4. **Rounding each share loses money.** `100.00 / 3` rounded three times is `99.99`. The
   largest-remainder method floors every share first and then hands the leftover units to the
   largest fractional remainders — exact by construction, then verified by summing the parts.
5. **Ties need a rule.** Equal remainders go to the earliest share, so the same input produces
   the same output on every run instead of whatever the dict order happens to be.
6. **Negative amounts flip the sign, not the method.** The split runs on the absolute value and
   is re-signed afterwards, so `-100.00 / 3` is `-33.34, -33.33, -33.33`.
7. **A comma is not always a thousands separator.** `12,34 USD` is 12.34 in half of Europe.
   Blanket-stripping commas reads it as 1234 — a silent 100x error — so commas are accepted
   only when they group exactly three digits.
8. **`isinstance(True, int)` is `True`.** A boolean amount or ratio passes every plain
   `isinstance(x, int)` check, so both are refused explicitly.
9. **`round()` is banker's rounding.** `round(2.5)` is 2, not 3. `Money.times` with a `Decimal`
   and `percent()` round half to even once, at the end, and say so.
10. **`Money` is not orderable across currencies.** No `order=True`, no `__lt__`: comparing
    `100 JPY` with `100 USD` has no answer, and tuple comparison would invent one.

## Layout

| path | what is in it |
| ---- | ------------- |
| `src/{{ package_name }}/model.py` | `Currency`, the currency table, `Money` |
| `src/{{ package_name }}/parse.py` | text to minor units, with the rounding mode made explicit |
| `src/{{ package_name }}/allocation.py` | the largest-remainder allocator and `split` |
| `src/{{ package_name }}/selftest.py` | every claim above, checked |
