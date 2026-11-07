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
check_equal "the version exits zero" 0 "$STATUS"
check_contains "the banner carries the version" "0.1.0" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists the subcommands" "selftest" "$OUT"

# --- membership ------------------------------------------------------------------
run "$PY" -m "$MODULE" has --words fixtures/words.txt cart
check_equal "a held word exits zero" 0 "$STATUS"
check_contains "the word answers as a word" "cart             word" "$OUT"

run "$PY" -m "$MODULE" has --words fixtures/words.txt zebra
check_equal "an absent word exits one" 1 "$STATUS"
check_contains "the absence is named" "zebra            not a word" "$OUT"

run "$PY" -m "$MODULE" has --words fixtures/words.txt cart cat
check_equal "every word asked must be held" 0 "$STATUS"

run "$PY" -m "$MODULE" has --words fixtures/words.txt cart zebra
check_equal "one absent word fails the batch" 1 "$STATUS"

# --- prefix listing -----------------------------------------------------------------
run "$PY" -m "$MODULE" prefix --words fixtures/words.txt --prefix cart
check_equal "a listing exits zero" 0 "$STATUS"
check_contains "cart comes first" "  cart" "$OUT"
check_contains "cartwheel follows" "  cartwheel" "$OUT"

run "$PY" -m "$MODULE" prefix --words fixtures/words.txt --prefix cart --json
SHAPE=$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["listing"])' "$OUT")
check_equal "the listing is sorted" "['cart', 'cartwheel']" "$SHAPE"

run "$PY" -m "$MODULE" prefix --words fixtures/words.txt --prefix zz
check_equal "an empty stem lists nothing" 1 "$STATUS"
check_contains "the emptiness is admitted" "under      0 word(s)" "$OUT"

# --- the words the gate refuses -------------------------------------------------------
run "$PY" -m "$MODULE" has --words fixtures/words.txt Cart
check_equal "uppercase is refused by name" 2 "$STATUS"
check_contains "the refusal names the word" "not lowercase" "$OUT"

run "$PY" -m "$MODULE" count --words "$WORK/missing.txt"
check_equal "a missing word list is unusable" 2 "$STATUS"
check_contains "the file is named" "no such word list" "$OUT"

NOISE="$WORK/noise.txt"
printf 'cart\ncar1\n' >"$NOISE"
run "$PY" -m "$MODULE" count --words "$NOISE"
check_equal "a noisy word list is unusable" 2 "$STATUS"
check_contains "the noise is named" "non-letter" "$OUT"

# --- building and deleting ---------------------------------------------------------------
WORDS="$WORK/words.txt"
printf '# a comment\n\ncar\ncart\ndog\n' >"$WORDS"
run "$PY" -m "$MODULE" add --words "$WORDS" kitten
check_equal "an add exits zero" 0 "$STATUS"
check_contains "the trie names its size" "words      4 held" "$OUT"

run "$PY" -m "$MODULE" delete --words "$WORDS" dog
check_equal "a delete exits zero" 0 "$STATUS"
check_contains "the delete lands" "deleted    True, 2 remain" "$OUT"

run "$PY" -m "$MODULE" delete --words "$WORDS" kitten
check_equal "a word the list never held escapes" 1 "$STATUS"

run "$PY" -m "$MODULE" prefix --words "$WORDS" --prefix ca
check_contains "the stem keeps its words" "cart" "$OUT"

# --- count and the shared stem ------------------------------------------------------------
run "$PY" -m "$MODULE" count --words fixtures/words.txt
check_equal "the count exits zero" 0 "$STATUS"
check_contains "the count names the size" "words      51 held" "$OUT"
check_contains "strangers share nothing" "prefix     '' shared by all" "$OUT"

# --- the fixture corpus --------------------------------------------------------------------
COUNT=$(grep -cv '^\s*\(#\|$\)' fixtures/words.txt)
if [[ "$COUNT" -ge 40 ]]; then
  ok "the fixture holds a corpus ($COUNT words)"
else
  bad "the fixture is too small ($COUNT words)"
fi

# --- the stories and the invariants -----------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
