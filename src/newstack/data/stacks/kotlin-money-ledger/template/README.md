# {{ title }}

{{ description }}

## Usage

```sh
printf 'cash,100.00\ninventory,-40.00\ncash,-12.50\n' > ledger.csv
gradle run --args=ledger.csv
gradle test
```

Amounts are `java.math.BigDecimal` end to end, so `0.10 + 0.10 + 0.10` is exactly
`0.30`. `Money` refuses to combine two currencies, `Ledger.report()` returns
sorted `account amount` lines, and `trialBalance()` totals every account (a
balanced double entry book totals zero).
