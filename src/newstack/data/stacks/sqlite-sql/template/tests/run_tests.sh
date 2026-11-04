#!/bin/sh
# Builds a scratch database and checks the numbers the README quotes.
set -u

root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root" || exit 1

work=$root/tests/.tmp
rm -rf "$work"
mkdir -p "$work"
db=$work/test.db

passed=0
failed=0
ok () { passed=$((passed + 1)); }
bad () { failed=$((failed + 1)); printf 'FAIL %s\n' "$1"; }

check () { # name actual expected
    if [ "$2" = "$3" ]; then ok; else bad "$1 (got [$2], want [$3])"; fi
}

sqlite3 "$db" < schema.sql || exit 1
sqlite3 "$db" < views.sql || exit 1
sqlite3 "$db" < seed.sql || exit 1

q () { sqlite3 -batch -separator '|' "$db" "$1"; }

# 1. the data that the reports are built on
check "integrity" "$(q 'PRAGMA integrity_check;')" "ok"
check "customer rows" "$(q 'SELECT COUNT(*) FROM customers;')" "4"
check "order rows" "$(q 'SELECT COUNT(*) FROM orders;')" "5"
check "item rows" "$(q 'SELECT COUNT(*) FROM order_items;')" "7"

# 2. the views do the arithmetic once
check "order 10 cents" "$(q 'SELECT cents FROM order_totals WHERE order_id = 10;')" "2100"
check "asha cents" "$(q "SELECT cents FROM customer_revenue WHERE name = 'Asha';")" "4350"
check "bruno cents" "$(q "SELECT cents FROM customer_revenue WHERE name = 'Bruno';")" "8700"
check "chen cents" "$(q "SELECT cents FROM customer_revenue WHERE name = 'Chen';")" "8250"
check "dana cents" "$(q "SELECT cents FROM customer_revenue WHERE name = 'Dana';")" "0"
check "revenue total" "$(q 'SELECT SUM(cents) FROM customer_revenue;')" "21300"

# 3. the constraints actually refuse bad rows
refused () { # name sql
    # Foreign keys are off by default in SQLite, so every connection that
    # expects them has to ask.
    if sqlite3 "$db" "PRAGMA foreign_keys = ON; $2" >/dev/null 2>&1; then bad "$1 (accepted)"; else ok; fi
}
refused "unknown country refused" \
    "INSERT INTO customers (id, name, country) VALUES (9, 'Eve', 'FR');"
refused "zero quantity refused" \
    "INSERT INTO order_items (order_id, sku, quantity, unit_price_cents) VALUES (10, 'BAD-1', 0, 100);"
refused "bad date refused" \
    "INSERT INTO orders (id, customer_id, placed_on) VALUES (99, 1, '15/03/2026');"
refused "duplicate line refused" \
    "INSERT INTO order_items (order_id, sku, quantity, unit_price_cents) VALUES (10, 'TEA-1', 1, 450);"
refused "order without a customer refused" \
    "INSERT INTO orders (id, customer_id, placed_on) VALUES (98, 77, '2026-04-01');"

# 4. and the cascade cleans up after itself
sqlite3 "$db" "PRAGMA foreign_keys = ON; DELETE FROM customers WHERE id = 1;" || bad "cascade delete errored"
check "orders after cascade" "$(q 'SELECT COUNT(*) FROM orders;')" "3"
check "items after cascade" "$(q 'SELECT COUNT(*) FROM order_items;')" "4"

# 5. a fresh database for the reports, then the CLI on top of it
sqlite3 "$db" < seed.sql || exit 1
check "top customers" "$("$root/bin/{{ npm_name }}" top_customers)" \
    "Bruno|2|87.00
Chen|1|82.50
Asha|2|43.50
Dana|0|0.00"
check "monthly report" "$("$root/bin/{{ npm_name }}" monthly)" \
    "2026-01|1|21.00
2026-02|2|61.50
2026-03|2|130.50"
check "countries report" "$("$root/bin/{{ npm_name }}" countries)" \
    "DE|87.00
US|82.50
IN|43.50"
check "query list" "$("$root/bin/{{ npm_name }}" --list | tr '\n' ' ')" "countries monthly top_customers "
check "version" "$("$root/bin/{{ npm_name }}" --version)" "0.1.0"

"$root/bin/{{ npm_name }}" nope >/dev/null 2>"$work/err"
check "unknown query status" "$?" "2"
check "unknown query message" "$(sed -n 1p "$work/err")" "{{ npm_name }}: no such query: nope"

rm -rf "$work"
checks=$((passed + failed))
printf 'checks: %s, passed: %s, failed: %s\n' "$checks" "$passed" "$failed"
[ "$failed" -eq 0 ] || exit 1
