#!/usr/bin/env bash
# Smoking gun for the flags: every check here is a claim the README makes.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
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

check() {
    local name="$1"
    shift
    if "$@" >"$WORK/out" 2>"$WORK/err"; then
        ok "$name"
    else
        bad "$name (exit $?)"
        sed 's/^/        /' "$WORK/out" "$WORK/err"
    fi
}

check_status() {
    local name="$1" want="$2"
    shift 2
    "$@" >"$WORK/out" 2>"$WORK/err"
    local got=$?
    if [ "$got" -eq "$want" ]; then
        ok "$name"
    else
        bad "$name (wanted exit $want, got $got)"
        sed 's/^/        /' "$WORK/out" "$WORK/err"
    fi
}

check_has() {
    local name="$1" needle="$2"
    shift 2
    "$@" >"$WORK/out" 2>"$WORK/err"
    if grep -qF -- "$needle" "$WORK/out"; then
        ok "$name"
    else
        bad "$name (no \"$needle\")"
        sed 's/^/        /' "$WORK/out" "$WORK/err"
    fi
}

run() {
    "$PY" -m "$MODULE" "$@"
}

# --- the banner is the program name, not the module name
check_has "the version banner names the program" "$PROGRAM" run --version

# --- listing
if [ "$(run list | wc -l)" -eq 5 ]; then
    ok "list names all five flags"
else
    bad "list names all five flags"
fi

# --- a full rollout is on, a kill switch is off
check_has "a 100% flag is on" "on  inside" run check dark-mode --user alice
check_status "a 100% flag exits 0" 0 run check dark-mode --user alice
check_has "a disabled flag is off" "off off" run check kill-switch-test --user alice
check_status "a disabled flag exits 1" 1 run check kill-switch-test --user alice

# --- targeting beats a zero rollout
check_has "a targeted user is on" "on  targeted" run check vip-access --user alice
check_status "a targeted user exits 0" 0 run check vip-access --user alice
check_has "an untargeted user is outside" "outside" run check vip-access --user carol
check_status "an untargeted user exits 1" 1 run check vip-access --user carol

# --- the decision explains itself
check_has "explain shows the cutoff" "cutoff   1000 (rollout 10%)" run explain checkout-redesign --user alice
check_has "explain shows the bucket" "bucket   " run explain checkout-redesign --user alice

# --- the bucket does not move between processes
first="$(PYTHONHASHSEED=1 "$PY" -m "$MODULE" explain checkout-redesign --user alice | grep '^bucket')"
second="$(PYTHONHASHSEED=99999 "$PY" -m "$MODULE" explain checkout-redesign --user alice | grep '^bucket')"
if [ -n "$first" ] && [ "$first" = "$second" ]; then
    ok "the bucket survives a different PYTHONHASHSEED"
else
    bad "the bucket survives a different PYTHONHASHSEED"
    printf '        first:  %s\n        second: %s\n' "$first" "$second"
fi

# --- unknown flags are a reason, not a crash
check_has "an unknown flag says unknown" "unknown" run check no-such-flag --user alice
check_status "an unknown flag exits 1" 1 run check no-such-flag --user alice

# --- distribution measures the population it claims to
run distribution --users 2000 >"$WORK/dist1" 2>"$WORK/err"
if grep -qF "worst deviation" "$WORK/dist1"; then
    ok "distribution reports a worst deviation"
else
    bad "distribution reports a worst deviation"
    sed 's/^/        /' "$WORK/dist1" "$WORK/err"
fi
run distribution --users 2000 >"$WORK/dist2" 2>"$WORK/err"
if cmp -s "$WORK/dist1" "$WORK/dist2"; then
    ok "distribution is reproducible"
else
    bad "distribution is reproducible"
fi

# --- misuse
check_status "zero users is refused" 2 run distribution --users 0
check_status "a missing flags file is refused" 2 run --flags "$WORK/absent.toml" list
cat >"$WORK/typo.toml" <<'TOML'
[[flag]]
name = "a"
salt = "s"
rolout = 9
TOML
run --flags "$WORK/typo.toml" list >"$WORK/out" 2>"$WORK/err"
if grep -qF "unknown key" "$WORK/err"; then
    ok "a typo names the unknown key"
else
    bad "a typo names the unknown key"
    sed 's/^/        /' "$WORK/out" "$WORK/err"
fi

# --- the implementation checks itself
check_has "selftest passes" "0 failed" run selftest

printf '\n%d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then
    printf 'smoke: FAILED\n'
    exit 1
fi
printf 'smoke: all checks passed\n'
