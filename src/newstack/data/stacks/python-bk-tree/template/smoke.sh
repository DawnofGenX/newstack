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

# --- the distance -------------------------------------------------------------
run "$PY" -m "$MODULE" distance ab ba
check_equal "the distance exits zero" 0 "$STATUS"
check_contains "plain edits count two" "edits      2" "$OUT"
check_contains "osa folds the swap into one" "with osa   1" "$OUT"

run "$PY" -m "$MODULE" distance kitten sitting
check_contains "kitten and sitting are three apart" "edits      3" "$OUT"

run "$PY" -m "$MODULE" distance abc abc
check_contains "a word is zero from itself" "edits      0" "$OUT"

run "$PY" -m "$MODULE" distance a b --limit -1
check_equal "a negative limit is unusable" 2 "$STATUS"
check_contains "the limit is named" "below zero" "$OUT"

# --- searching a word list ------------------------------------------------------
WORDS="$WORK/words.txt"
printf 'hello\nhallo\nhelp\nhelm\nzzz\n' >"$WORDS"

run "$PY" -m "$MODULE" search --words "$WORDS" --word hello --distance 1
check_equal "a found search exits zero" 0 "$STATUS"
check_contains "the near neighbour is named" "hallo" "$OUT"

run "$PY" -m "$MODULE" search --words "$WORDS" --word hello --distance 0
check_contains "radius zero finds the word itself" "  0  hello" "$OUT"

run "$PY" -m "$MODULE" search --words "$WORDS" --word qqqq --distance 1
check_equal "an empty search exits one" 1 "$STATUS"
check_contains "the verdict is stated" "nothing within that distance" "$OUT"

run "$PY" -m "$MODULE" search --words "$WORDS" --word help --distance 1 --json
check_equal "search --json exits zero" 0 "$STATUS"
SHAPE=$("$PY" -c 'import json,sys; payload=json.loads(sys.argv[1]); print(payload["query"], "hits" in payload)' "$OUT")
check_equal "search --json is only json" "help True" "$SHAPE"

run "$PY" -m "$MODULE" search --words "$WORDS" --word hello --distance 1 --json --transpositions
check_equal "transposed search exits zero" 0 "$STATUS"
SCANED=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["full_scan"])' "$OUT")
check_equal "transpositions force the honest scan" "True" "$SCANED"

run "$PY" -m "$MODULE" search --words "$WORK/missing.txt" --word a --distance 1
check_equal "a missing word list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such word list" "$OUT"

# --- nearest and the shape ------------------------------------------------------
run "$PY" -m "$MODULE" nearest --words "$WORDS" --word hullo
check_equal "nearest always answers" 0 "$STATUS"
check_contains "the closest distance is stated" "closest    1" "$OUT"

run "$PY" -m "$MODULE" nearest --words "$WORDS" --word hello
check_contains "a word in the list is nearest to itself" "closest    0" "$OUT"

run "$PY" -m "$MODULE" tree --words "$WORDS"
check_equal "the tree is printable" 0 "$STATUS"
check_contains "the walk and the scan agree" "same set   True" "$OUT"

run "$PY" -m "$MODULE" tree --words "$WORK/missing.txt"
check_equal "the tree needs a real file" 2 "$STATUS"

# --- the fixture corpus ----------------------------------------------------------
HITS=0
while IFS= read -r word; do
  [[ -z "$word" || "$word" == \#* ]] && continue
  HITS=$((HITS + 1))
  run "$PY" -m "$MODULE" nearest --words fixtures/words.txt --word "$word"
  if [[ "$STATUS" -eq 0 ]]; then ok "fixture $word has a nearest word"; else bad "fixture $word found nothing"; fi
done <fixtures/words.txt
if [[ "$HITS" -ge 20 ]]; then ok "the fixture holds a corpus ($HITS words)"; else bad "the fixture is too small ($HITS words)"; fi

# --- the stories and the invariants -----------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "stories      6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
