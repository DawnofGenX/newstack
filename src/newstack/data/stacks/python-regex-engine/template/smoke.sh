#!/usr/bin/env bash
# The smoke test runs the tool the way a user would and checks what it says.
# PY points at the interpreter that has this package installed.
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

check_contains() {
  local name="$1" needle="$2" text="$3"
  if [[ "$text" == *"$needle"* ]]; then
    ok "$name"
  else
    bad "$name"
    printf '       wanted %q in %q\n' "$needle" "${text:0:200}"
  fi
}

check_equal() {
  local name="$1" want="$2" got="$3"
  if [[ "$want" == "$got" ]]; then
    ok "$name"
  else
    bad "$name"
    printf '       wanted %q, got %q\n' "$want" "$got"
  fi
}

run() {
  OUT=$("$@" 2>&1)
  STATUS=$?
}

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "smoke: $PROGRAM"

run "$PY" -m "$MODULE" --version
check_equal "the version names the program" 0 "$STATUS"
check_contains "the banner carries the version" "0.1.0" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists the subcommands" "selftest" "$OUT"

# --- matching the whole text -------------------------------------------------
run "$PY" -m "$MODULE" match 'a*b' 'aaab'
check_equal "a star matches the whole text" 0 "$STATUS"
check_contains "the verdict is stated" "the whole text matches" "$OUT"

run "$PY" -m "$MODULE" match 'a*b' 'aaa'
check_equal "a miss exits one" 1 "$STATUS"
check_contains "a miss says so" "no match for the whole text" "$OUT"

run "$PY" -m "$MODULE" match 'ab' 'abc'
check_equal "a prefix is not a whole match" 1 "$STATUS"

# --- searching ---------------------------------------------------------------
run "$PY" -m "$MODULE" search 'a+' 'xaay'
check_equal "a search finds the run" 0 "$STATUS"
check_contains "the search reports its span" "[1, 3) 'aa'" "$OUT"

run "$PY" -m "$MODULE" search 'ab|abc' 'zabc'
check_contains "the search is leftmost then longest" "[1, 4) 'abc'" "$OUT"

run "$PY" -m "$MODULE" search 'q' 'abc'
check_equal "a search that finds nothing exits one" 1 "$STATUS"

# --- the machine -------------------------------------------------------------
run "$PY" -m "$MODULE" machine 'a*b'
check_equal "the machine is printable" 0 "$STATUS"
check_contains "silent edges are counted" "5 of them silent" "$OUT"
check_contains "the accepting state is named" "(no way out)" "$OUT"

run "$PY" -m "$MODULE" explain '(cat|dog)s?' 'dogs'
check_equal "the trace exits zero" 0 "$STATUS"
check_contains "the trace has a header" "seen" "$OUT"
check_contains "an accepting row is marked" "yes" "$OUT"

run "$PY" -m "$MODULE" why '(a*)*b' 'aaaaaaaaaaaaaa'
check_equal "why reports a miss" 1 "$STATUS"
check_contains "why gives a reason" "no accepting state survived" "$OUT"
check_contains "why shows the set the pass carried" "try one by one" "$OUT"

run "$PY" -m "$MODULE" dfa '(a|b)*abb'
check_equal "the determinised machine is printable" 0 "$STATUS"
check_contains "the dfa counts its states" "state(s)" "$OUT"
check_contains "the dfa names the catch-all symbol" "plus" "$OUT"

run "$PY" -m "$MODULE" dfa '(a|b)*abb' --json
check_equal "dfa --json exits zero" 0 "$STATUS"
SHAPE=$("$PY" -c 'import json,sys; payload=json.loads(sys.argv[1]); print(payload["pattern"], payload["states"] > 0)' "$OUT")
check_equal "dfa --json is only json" "(a|b)*abb True" "$SHAPE"

run "$PY" -m "$MODULE" match 'ab' 'ab' --json
check_equal "match --json exits zero" 0 "$STATUS"
SHAPE=$("$PY" -c 'import json,sys; payload=json.loads(sys.argv[1]); print(payload["start"], payload["end"], payload["value"])' "$OUT")
check_equal "match --json carries the span" "0 2 ab" "$SHAPE"

# --- the two machines ---------------------------------------------------------
run "$PY" -m "$MODULE" agrees '(a|b)*abb' --alphabet ab --max-len 5
check_equal "the exhaustive check exits zero" 0 "$STATUS"
check_contains "the check counts the strings" "63 string(s)" "$OUT"
check_contains "the check states its verdict" "the two machines agree" "$OUT"

run "$PY" -m "$MODULE" agrees 'a' --max-len -1
check_equal "a negative length is unusable" 2 "$STATUS"
check_contains "the length is named" "--max-len" "$OUT"

run "$PY" -m "$MODULE" compare '(a*)*b' 'aaaaaaaaaaaaaa'
check_equal "the comparison exits zero when they agree" 0 "$STATUS"
check_contains "the comparison counts the steps" "step(s)" "$OUT"
check_contains "the pass costs one sweep" "set(s)" "$OUT"
check_contains "the comparison states its verdict" "both engines agree" "$OUT"

# --- what is refused ----------------------------------------------------------
run "$PY" -m "$MODULE" match 'a)' 'a'
check_equal "a stray bracket is unusable" 2 "$STATUS"
check_contains "the bracket is explained" "has no place here" "$OUT"
check_contains "the caret points at the character" "^" "$OUT"

run "$PY" -m "$MODULE" match '' ''
check_equal "an empty pattern is refused" 2 "$STATUS"
check_contains "the refusal says what to write" "use () for nothing" "$OUT"

run "$PY" -m "$MODULE" match '[z-a]' 'z'
check_equal "a backwards range is refused" 2 "$STATUS"
check_contains "the range is named" "runs backwards" "$OUT"

run "$PY" -m "$MODULE" match 'a{2}' 'aa'
check_equal "counted repetition is refused" 2 "$STATUS"
check_contains "the refusal offers the alternative" "write the copies" "$OUT"

run "$PY" -m "$MODULE" match '(ab' 'ab'
check_equal "an unclosed group is refused" 2 "$STATUS"
check_contains "the group position is named" "never closed" "$OUT"

# --- the fixture corpus -------------------------------------------------------
ROWS=0
while IFS=$'\t' read -r pattern text want; do
  [[ -z "$pattern" || "$pattern" == \#* ]] && continue
  ROWS=$((ROWS + 1))
  run "$PY" -m "$MODULE" match "$pattern" "$text"
  if [[ "$want" == "yes" ]]; then
    if [[ "$STATUS" -eq 0 ]]; then ok "fixture $ROWS $pattern matches $text"; else bad "fixture $ROWS $pattern should match $text"; fi
  else
    if [[ "$STATUS" -eq 1 ]]; then ok "fixture $ROWS $pattern refuses $text"; else bad "fixture $ROWS $pattern should refuse $text"; fi
  fi
done < fixtures/patterns.txt
if [[ "$ROWS" -ge 10 ]]; then ok "the fixture holds a corpus ($ROWS rows)"; else bad "the fixture is too small ($ROWS rows)"; fi

# --- the stories and the invariants -------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "stories      6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
