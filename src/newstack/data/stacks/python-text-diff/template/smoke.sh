#!/usr/bin/env bash
# Prove the tool against real files: no mocks, no in-process shortcuts.
set -uo pipefail

MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
PY="${PY:-.venv/bin/python}"
WORK="$(mktemp -d)"
PASSED=0
FAILED=0

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

ok() { PASSED=$((PASSED + 1)); printf 'ok    %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf 'FAIL  %s\n' "$1"; }
run() { "$@" >"$WORK/out" 2>"$WORK/err"; STATUS=$?; }
expect() {
  local label="$1" want="$2"
  if [ "$STATUS" -eq "$want" ]; then ok "$label"; else
    bad "$label (exit $STATUS, wanted $want)"; sed -n '1,3s/^/      /p' "$WORK/err"
  fi
}
contains() {
  local label="$1" needle="$2" file="$3"
  if grep -qF -- "$needle" "$file"; then ok "$label"; else
    bad "$label (no '$needle')"; sed -n '1,3s/^/      /p' "$file"
  fi
}

printf 'line 1\nline 2\nline 3\nline 4\n' >"$WORK/a.txt"
printf 'line 1\nline two\nline 3\nline 4\n' >"$WORK/b.txt"
printf 'line 1\nbut different\nline 3\n' >"$WORK/drift.txt"
printf 'same\nsame\n' >"$WORK/twice.txt"
printf 'a\nb' >"$WORK/nonl.txt"

run "$PY" -m "$MODULE" --version
expect "version exits 0" 0
contains "the banner names the program" "$PROGRAM" "$WORK/out"

run "$PY" -m "$MODULE" --help
expect "help exits 0" 0
contains "the help lists diff" "diff" "$WORK/out"
contains "the help lists apply" "apply" "$WORK/out"
contains "the help lists check" "check" "$WORK/out"

run "$PY" -m "$MODULE" diff "$WORK/a.txt" "$WORK/b.txt"
expect "diff exits 0" 0
contains "the diff names the old file" "--- $WORK/a.txt" "$WORK/out"
contains "the diff has a hunk header" "@@ -1,4 +1,4 @@" "$WORK/out"
contains "the diff removes the old line" "-line 2" "$WORK/out"
contains "the diff adds the new line" "+line two" "$WORK/out"

run "$PY" -m "$MODULE" diff "$WORK/a.txt" "$WORK/b.txt" -o "$WORK/c.patch"
expect "diff -o exits 0" 0
contains "the file was written" "wrote" "$WORK/err"
if [ -s "$WORK/c.patch" ]; then ok "the patch file has content"; else bad "the patch file is empty"; fi

run "$PY" -m "$MODULE" diff "$WORK/a.txt" "$WORK/a.txt"
expect "a diff of one file with itself is not a failure" 0
contains "and it says so" "no differences" "$WORK/err"

run "$PY" -m "$MODULE" apply "$WORK/a.txt" "$WORK/c.patch"
expect "apply exits 0" 0
contains "apply prints the patched text" "line two" "$WORK/out"
contains "apply reports a clean fit" "applied   clean" "$WORK/err"
if cmp -s "$WORK/out" "$WORK/b.txt"; then ok "the patched text is byte-identical"; else bad "the patched text differs"; fi

cp "$WORK/a.txt" "$WORK/inplace.txt"
run "$PY" -m "$MODULE" apply "$WORK/inplace.txt" "$WORK/c.patch" -i
expect "apply -i exits 0" 0
if cmp -s "$WORK/inplace.txt" "$WORK/b.txt"; then ok "apply -i rewrote the file"; else bad "apply -i did not rewrite"; fi

run "$PY" -m "$MODULE" apply "$WORK/drift.txt" "$WORK/c.patch"
expect "a patch that does not fit is exit 2" 2
contains "and the message names the line" "does not apply" "$WORK/err"

printf 'same\nsame\n' >"$WORK/same.txt"
printf -- '--- a\n+++ b\n@@ -5 +5 @@\n-same\n+other\n' >"$WORK/amb.patch"
run "$PY" -m "$MODULE" apply "$WORK/same.txt" "$WORK/amb.patch"
expect "a hunk that matches twice is exit 2" 2
contains "and it names both places" "matches at lines 1 and 2" "$WORK/err"

printf 'hello\n' >"$WORK/bad.patch"
run "$PY" -m "$MODULE" apply "$WORK/a.txt" "$WORK/bad.patch"
expect "a malformed patch is exit 2" 2
contains "and it says what it is not" "not a unified diff" "$WORK/err"

run "$PY" -m "$MODULE" diff "$WORK/missing.txt" "$WORK/a.txt"
expect "a missing file is exit 2" 2
contains "and it says it cannot read" "cannot read" "$WORK/err"

run "$PY" -m "$MODULE" diff "$WORK/nonl.txt" "$WORK/b.txt" -o "$WORK/nonl.patch"
expect "a file without a final newline diffs" 0
contains "the marker is in the patch" "No newline at end of file" "$WORK/nonl.patch"

run "$PY" -m "$MODULE" diff "$WORK/a.txt" "$WORK/b.txt" --context 0 -o "$WORK/c0.patch"
expect "context zero diffs" 0
if grep -qF -- " line 1" "$WORK/c0.patch"; then
  bad "context zero kept a context line"
else ok "context zero keeps no context line"; fi

run "$PY" -m "$MODULE" check "$WORK/a.txt" "$WORK/b.txt"
expect "check exits 0" 0
contains "check proves the round trip" "apply reproduces the new text" "$WORK/out"
contains "check ends with a verdict" "all three claims hold" "$WORK/out"
CLAIMS=$(grep -c '^ok  ' "$WORK/out")
if [ "$CLAIMS" -eq 3 ]; then ok "check reported three claims"; else
  bad "check reported $CLAIMS claim(s)"; fi

run "$PY" -m "$MODULE" demo
expect "demo exits 0" 0
contains "every scenario holds" "0 not as advertised" "$WORK/out"

run "$PY" -m "$MODULE" selftest
expect "selftest exits 0" 0
contains "the selftest reports no failures" "0 failed" "$WORK/out"

run "$PY" -m "$MODULE"
expect "no command is exit 2" 2

run "$PY" -m "$MODULE" nope
expect "an unknown command is exit 2" 2

printf 'x\r\ny\r\n' >"$WORK/crlf.txt"
printf 'x\r\nz\r\n' >"$WORK/crlf2.txt"
run "$PY" -m "$MODULE" diff "$WORK/crlf.txt" "$WORK/crlf2.txt" -o "$WORK/crlf.patch"
expect "a CRLF file diffs" 0
run "$PY" -m "$MODULE" apply "$WORK/crlf.txt" "$WORK/crlf.patch"
expect "the CRLF patch applies" 0
if cmp -s "$WORK/out" "$WORK/crlf2.txt"; then ok "CRLF endings survived"; else bad "CRLF endings changed"; fi

printf '\n%d passed, %d failed\n' "$PASSED" "$FAILED"
if [ "$FAILED" -eq 0 ]; then echo "smoke: all checks passed"; exit 0; fi
echo "smoke: FAILED"
exit 1
