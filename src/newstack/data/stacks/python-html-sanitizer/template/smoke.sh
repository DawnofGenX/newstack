#!/usr/bin/env bash
# Real processes, real files: the CLI is what a pipeline calls.
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
lacks() {
  local label="$1" needle="$2" file="$3"
  if grep -qF -- "$needle" "$file"; then bad "$label (found '$needle')"; else ok "$label"; fi
}

printf '<p onclick="steal()">hi</p>' >"$WORK/page.html"
printf '<p>ok</p><script>alert(1)</script>' >"$WORK/script.html"
printf '<a href="javascript:alert(1)">x</a>' >"$WORK/url.html"
printf '<a href="jav&#x09;ascript&#58;alert(1)">x</a>' >"$WORK/hidden.html"
printf '<a href="https://example.com/a">good</a>' >"$WORK/good.html"
printf '<b><i>odd</b></i>' >"$WORK/odd.html"
printf '5 < 6 & 7 > 2' >"$WORK/text.html"
printf '\xff\xfe\x00bad' >"$WORK/binary.html"

run "$PY" -m "$MODULE" --version
expect "version exits 0" 0
contains "the banner names the program" "$PROGRAM" "$WORK/out"

run "$PY" -m "$MODULE" render --file "$WORK/page.html"
expect "render exits 0" 0
contains "the element survives" "<p>hi</p>" "$WORK/out"
lacks "the handler does not" "onclick" "$WORK/out"

run "$PY" -m "$MODULE" render --file "$WORK/script.html"
expect "a script block exits 0" 0
contains "the paragraph is kept" "<p>ok</p>" "$WORK/out"
lacks "the payload is gone" "alert" "$WORK/out"

run "$PY" -m "$MODULE" render --file "$WORK/url.html"
expect "a javascript url exits 0" 0
contains "the link is kept" "<a>x</a>" "$WORK/out"
lacks "the scheme is gone" "javascript" "$WORK/out"

run "$PY" -m "$MODULE" render --file "$WORK/hidden.html"
expect "a hidden scheme exits 0" 0
lacks "the entity-encoded scheme is refused" "script" "$WORK/out"

run "$PY" -m "$MODULE" render --file "$WORK/good.html"
expect "a good url exits 0" 0
contains "a named scheme survives" 'href="https://example.com/a"' "$WORK/out"

run "$PY" -m "$MODULE" render --file "$WORK/odd.html"
expect "unbalanced markup exits 0" 0
contains "the output is closed inside out" "<b><i>odd</i></b>" "$WORK/out"

run "$PY" -m "$MODULE" render --file "$WORK/text.html"
expect "text that looks like markup exits 0" 0
contains "the angle brackets are escaped" "5 &lt; 6 &amp; 7 &gt; 2" "$WORK/out"

run "$PY" -m "$MODULE" render --file "$WORK/page.html" --json
expect "render --json exits 0" 0
contains "the json carries the output" '"output": "<p>hi</p>"' "$WORK/out"
contains "the json carries the counters" '"attributes_dropped": 1' "$WORK/out"

printf '<b>piped</b>' | "$PY" -m "$MODULE" render >"$WORK/out" 2>"$WORK/err"
STATUS=$?
expect "render reads stdin" 0
contains "stdin was sanitized" "<b>piped</b>" "$WORK/out"

run "$PY" -m "$MODULE" render --file "$WORK/binary.html"
expect "a non-UTF-8 file is exit 2" 2
contains "and it says so" "is not UTF-8" "$WORK/err"

run "$PY" -m "$MODULE" render --file "$WORK/missing.html"
expect "a missing file is exit 2" 2
contains "and it says it cannot read" "cannot read" "$WORK/err"

run "$PY" -m "$MODULE" check "$WORK/page.html" "$WORK/good.html"
expect "check exits 0 on a clean corpus" 0
contains "each file is reported" "ok       $WORK/page.html" "$WORK/out"

run "$PY" -m "$MODULE" policy
expect "policy exits 0" 0
contains "the anchor allowlist is printed" "a: href title" "$WORK/out"
contains "the schemes are printed" "schemes  http https mailto tel" "$WORK/out"

run "$PY" -m "$MODULE" demo
expect "demo exits 0" 0
contains "eight vectors ran" "8 vectors" "$WORK/out"
contains "none of them misbehaved" "0 not as advertised" "$WORK/out"

run "$PY" -m "$MODULE" selftest
expect "selftest exits 0" 0
contains "the selftest reports no failures" "0 failed" "$WORK/out"

run "$PY" -m "$MODULE"
expect "no command is exit 2" 2
run "$PY" -m "$MODULE" nope
expect "an unknown command is exit 2" 2

printf '\n%d passed, %d failed\n' "$PASSED" "$FAILED"
if [ "$FAILED" -eq 0 ]; then echo "smoke: all checks passed"; exit 0; fi
echo "smoke: FAILED"
exit 1
