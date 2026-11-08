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
run "$PY" -m "$MODULE" comb 1 2 3; check_equal "comb exits zero" 0 "$STATUS"; check_contains "comb line" "combs" "$OUT"
run "$PY" -m "$MODULE" comb --json 1 2; check_equal "json comb exits zero" 0 "$STATUS"
run "$PY" -m "$MODULE" count 4; check_equal "count exits zero" 0 "$STATUS"; check_contains "count line" "count" "$OUT"
run "$PY" -m "$MODULE" unique 1 1 2; check_equal "unique exits zero" 0 "$STATUS"
run "$PY" -m "$MODULE" comb 1 2 3 4 5 6 7 8 9; check_equal "oversized exits two" 2 "$STATUS"
run "$PY" -m "$MODULE" demo; check_equal "demo exits zero" 0 "$STATUS"; check_contains "stories hold" "6 of 6 hold" "$OUT"
run "$PY" -m "$MODULE" selftest; check_equal "selftest exits zero" 0 "$STATUS"; check_contains "selftest no failures" "0 failed" "$OUT"
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"; [[ "$FAILED" -eq 0 ]]
