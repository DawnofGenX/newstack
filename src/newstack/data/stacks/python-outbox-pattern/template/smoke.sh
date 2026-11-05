#!/usr/bin/env bash
# Every check here is a claim the README makes about the outbox.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
DB="$WORK/outbox.db"
trap 'rm -rf "$WORK"' EXIT

passed=0
failed=0

ok() {
    printf 'ok    %s\n' "$1"
    passed=$((passed + 1))
}

bad() {
    printf 'FAIL  %s\n' "$1"
    failed=$((failed + 1))
}

run() {
    "$PY" -m "$MODULE" --db "$DB" "$@"
}

expect_status() {
    local description="$1" want="$2"
    shift 2
    "$@" >"$WORK/out" 2>"$WORK/err"
    local got=$?
    if [ "$got" -eq "$want" ]; then
        ok "$description"
    else
        bad "$description (wanted exit $want, got $got)"
        sed 's/^/        /' "$WORK/out" "$WORK/err"
    fi
}

expect_has() {
    local description="$1" needle="$2"
    shift 2
    "$@" >"$WORK/out" 2>"$WORK/err"
    if grep -qF -- "$needle" "$WORK/out"; then
        ok "$description"
    else
        bad "$description (no \"$needle\" in stdout)"
        sed 's/^/        /' "$WORK/out" "$WORK/err"
    fi
}

expect_err_has() {
    local description="$1" needle="$2"
    shift 2
    "$@" >"$WORK/out" 2>"$WORK/err"
    if grep -qF -- "$needle" "$WORK/err"; then
        ok "$description"
    else
        bad "$description (no \"$needle\" in stderr)"
        sed 's/^/        /' "$WORK/out" "$WORK/err"
    fi
}

# --- the banner names the program, not the module
if "$PY" -m "$MODULE" --version | grep -qF -- "$PROGRAM"; then
    ok "the version banner names the program"
else
    bad "the version banner names the program"
fi

# --- the write is one transaction
expect_has "placing an order commits a row" "placed  order 1 for 1200" run place --amount 1200
expect_has "and its event is pending" "pending: 2" run place --amount 1200
expect_has "show prints the order" "order    1      1200  placed" run show
expect_has "show counts the pending events" "2 order(s), 2 event(s) shown, 2 pending" run show

# --- the relay publishes and marks
expect_has "the relay publishes" "publish " run relay
expect_has "a second pass has nothing left" "relay   delivered 0, blocked 0" run relay
expect_has "nothing is pending afterwards" "0 pending" run show --pending

# --- the crash window
run place --amount 300 >/dev/null 2>&1
expect_status "a crash after the sink exits one" 1 run relay --crash-after 1
run relay --crash-after 1 >"$WORK/out" 2>"$WORK/err"
if grep -qF "crashed before marking" "$WORK/out"; then
    ok "the crash is reported with the event id"
else
    bad "the crash is reported with the event id"
    sed 's/^/        /' "$WORK/out" "$WORK/err"
fi
if grep -qF "died after the sink accepted it" "$WORK/err"; then
    ok "and stderr explains the window"
else
    bad "and stderr explains the window"
    sed 's/^/        /' "$WORK/err"
fi
expect_has "the event is still pending" "1 pending" run show --pending
expect_has "the retry delivers the same event again" "relay   delivered 1, blocked 0" run relay
expect_has "and then the outbox is clear" "0 pending" run show --pending

# --- paying appends an event, twice is refused
expect_has "paying appends an event" "event   " run pay 1
expect_status "paying twice exits two" 2 run pay 1
expect_err_has "and says why" "already paid" run pay 1

# --- misuse is loud
expect_status "a zero amount is refused" 2 run place --amount 0
expect_status "a missing command is refused" 2 run
expect_status "an unknown command is refused" 2 run frobnicate

# --- the demo is the argument
expect_has "the demo shows the loss" "outbox rows carrying the event: 0" run demo
expect_has "the demo shows exactly-once" "exactly once" run demo
expect_has "the demo shows ordering" "in order" run demo
expect_status "the demo exits zero when every scenario holds" 0 run demo

# --- an empty database is not an error
empty="$WORK/empty.db"
"$PY" -m "$MODULE" --db "$empty" show >"$WORK/out" 2>"$WORK/err"
if grep -qF "0 order(s), 0 event(s) shown, 0 pending" "$WORK/out"; then
    ok "an empty database shows nothing"
else
    bad "an empty database shows nothing"
    sed 's/^/        /' "$WORK/out" "$WORK/err"
fi

# --- the library checks itself
expect_has "selftest passes" "0 failed" run selftest

printf '\n%d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then
    printf 'smoke: FAILED\n'
    exit 1
fi
printf 'smoke: all checks passed\n'
