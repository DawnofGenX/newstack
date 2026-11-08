#!/usr/bin/env bash
set -uo pipefail
PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
PASSED=0; FAILED=0
ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }
check_contains() { local name="$1" needle="$2" text="$3"; if [[ "$text" == *"$needle"* ]]; then ok "$name"; else bad "$name"; printf '       wanted %q in %q\n' "$needle" "${text:0:200}"; fi; }
check_equal() { local name="$1" want="$2" got="$3"; if [[ "$want" == "$got" ]]; then ok "$name"; else bad "$name"; printf '       wanted %q, got %q\n' "$want" "$got"; fi; }
run() { OUT=$("$@" 2>&1); STATUS=$?; }
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
echo "smoke: $PROGRAM"
run "$PY" -m "$MODULE" --version; check_equal "version exits zero" 0 "$STATUS"; check_contains "banner version" "0.1.0" "$OUT"
run "$PY" -m "$MODULE" --help; check_equal "help exits zero" 0 "$STATUS"; check_contains "help subcommands" "selftest" "$OUT"
run "$PY" -m "$MODULE" greater 2 1 3; check_equal "greater exits zero" 0 "$STATUS"; check_contains "greater line" "greater" "$OUT"
run "$PY" -m "$MODULE" smaller 2 1 3; check_equal "smaller exits zero" 0 "$STATUS"; check_contains "smaller line" "smaller" "$OUT"
run "$PY" -m "$MODULE" previous 2 1 3; check_equal "previous exits zero" 0 "$STATUS"; check_contains "previous line" "previous" "$OUT"
run "$PY" -m "$MODULE" greater --json 2 1 3; check_equal "json greater exits zero" 0 "$STATUS"
run "$PY" -m "$MODULE" audit 2 1 3; check_equal "audit exits zero" 0 "$STATUS"; check_contains "audit line" "length" "$OUT"
run "$PY" -m "$MODULE" greater 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65; check_equal "oversized exits two" 2 "$STATUS"
run "$PY" -m "$MODULE" demo; check_equal "demo exits zero" 0 "$STATUS"; check_contains "stories hold" "of 6 hold" "$OUT"
run "$PY" -m "$MODULE" selftest; check_equal "selftest exits zero" 0 "$STATUS"; check_contains "selftest no failures" "0 failed" "$OUT"
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"; [[ "$FAILED" -eq 0 ]]
