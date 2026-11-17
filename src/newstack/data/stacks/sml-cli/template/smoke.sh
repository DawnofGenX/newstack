#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

if ! command -v mlton >/dev/null 2>&1; then
  echo "smoke: mlton is missing (install mlton)"
  exit 1
fi
if ! command -v wc >/dev/null 2>&1; then
  echo "smoke: wc is missing (install wc)"
  exit 1
fi

echo "smoke: sml-cli"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
make build
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "build"; else bad "build"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
make test
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_2.sh" <<'__STEP__'
make parity
__STEP__
run sh "$work/step_2.sh"
if [ "$STATUS" -eq 0 ]; then ok "parity"; else bad "parity"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_3.sh" <<'__STEP__'
./bin/{{ npm_name }} --help
__STEP__
run sh "$work/step_3.sh"
if [ "$STATUS" -eq 0 ]; then ok "help"; else bad "help"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_4.sh" <<'__STEP__'
./bin/{{ npm_name }} --bogus >/dev/null 2>&1; test $? -eq 2
__STEP__
run sh "$work/step_4.sh"
if [ "$STATUS" -eq 0 ]; then ok "usage-error"; else bad "usage-error"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_5.sh" <<'__STEP__'
./bin/{{ npm_name }} does-not-exist.txt >/dev/null 2>&1; test $? -eq 1
__STEP__
run sh "$work/step_5.sh"
if [ "$STATUS" -eq 0 ]; then ok "missing-file"; else bad "missing-file"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_6.sh" <<'__STEP__'
printf 'a b c\n' | ./bin/{{ npm_name }} | grep -q '1       3       6'
__STEP__
run sh "$work/step_6.sh"
if [ "$STATUS" -eq 0 ]; then ok "stdin"; else bad "stdin"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
