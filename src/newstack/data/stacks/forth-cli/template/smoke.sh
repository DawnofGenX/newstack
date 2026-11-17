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


echo "smoke: forth-cli"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
sh tests/run_tests.sh
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
./bin/{{ npm_name }} --help | grep -qF 'Usage: {{ npm_name }} [OPTION]... [FILE]...'
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "help"; else bad "help"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_2.sh" <<'__STEP__'
set +e; ./bin/{{ npm_name }} --bogus >/dev/null 2>&1; status=$?; echo "exit status: $status"; test "$status" -eq 2
__STEP__
run sh "$work/step_2.sh"
if [ "$STATUS" -eq 0 ]; then ok "usage-error"; else bad "usage-error"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_3.sh" <<'__STEP__'
set +e; ./bin/{{ npm_name }} nope.txt >/dev/null 2>&1; status=$?; echo "exit status: $status"; test "$status" -eq 1
__STEP__
run sh "$work/step_3.sh"
if [ "$STATUS" -eq 0 ]; then ok "missing-file"; else bad "missing-file"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_4.sh" <<'__STEP__'
set +e; out=$(printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w); status=$?; echo "stdin: $out"; test "$status" -eq 0; test "$out" = '3'
__STEP__
run sh "$work/step_4.sh"
if [ "$STATUS" -eq 0 ]; then ok "stdin"; else bad "stdin"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_5.sh" <<'__STEP__'
mkdir -p .parity; printf 'alpha beta\ngamma delta\n' > .parity/p1.txt; printf 'alpha beta\ngamma' > .parity/p2.txt; printf 'h\303\251llo w\303\266rld\n' > .parity/p3.txt; : > .parity/p4.txt; printf 'a\tb\vc\fd\n' > .parity/p5.txt; for f in .parity/p*.txt; do ours=$(./bin/{{ npm_name }} -l -w -c "$f"); theirs=$(wc -l -w -c "$f"); test "$ours" = "$theirs" || { echo "$f: $ours"; echo "wc:     $theirs"; exit 1; }; done
__STEP__
run sh "$work/step_5.sh"
if [ "$STATUS" -eq 0 ]; then ok "parity"; else bad "parity"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
