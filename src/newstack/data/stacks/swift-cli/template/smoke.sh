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

if ! command -v swift >/dev/null 2>&1; then
  echo "smoke: swift is missing (install swift)"
  exit 1
fi

echo "smoke: swift-cli"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
swift build
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "build"; else bad "build"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
swift test
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_2.sh" <<'__STEP__'
./bin/{{ npm_name }} --help
__STEP__
run sh "$work/step_2.sh"
if [ "$STATUS" -eq 0 ]; then ok "help"; else bad "help"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_3.sh" <<'__STEP__'
./bin/{{ npm_name }} --bogus >/dev/null 2>&1; test $? -eq 2
__STEP__
run sh "$work/step_3.sh"
if [ "$STATUS" -eq 0 ]; then ok "usage-error"; else bad "usage-error"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_4.sh" <<'__STEP__'
./bin/{{ npm_name }} does-not-exist.txt >/dev/null 2>&1; test $? -eq 1
__STEP__
run sh "$work/step_4.sh"
if [ "$STATUS" -eq 0 ]; then ok "missing-file"; else bad "missing-file"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_5.sh" <<'__STEP__'
test "$(printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w)" = '3 -'
__STEP__
run sh "$work/step_5.sh"
if [ "$STATUS" -eq 0 ]; then ok "stdin"; else bad "stdin"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_6.sh" <<'__STEP__'
printf 'alpha beta\ngamma delta\n' > .p1.txt && printf 'no trailing newline' > .p2.txt && printf 'h\303\251llo w\303\266rld\n' > .p3.txt && : > .p4.txt && printf 'a\tb\nc\vd\re\n' > .p5.txt && for f in .p1.txt .p2.txt .p3.txt .p4.txt .p5.txt; do ours=$(./bin/{{ npm_name }} -l -w -c "$f" | awk '{print $1, $2, $3}'); theirs=$(wc -l -w -c "$f" | awk '{print $1, $2, $3}'); if [ "$ours" != "$theirs" ]; then echo "MISMATCH $f: ours=[$ours] theirs=[$theirs]"; exit 1; fi; done && rm -f .p1.txt .p2.txt .p3.txt .p4.txt .p5.txt && echo "parity ok"
__STEP__
run sh "$work/step_6.sh"
if [ "$STATUS" -eq 0 ]; then ok "parity"; else bad "parity"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
