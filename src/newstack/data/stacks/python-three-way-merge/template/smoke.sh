#!/usr/bin/env bash
# End-to-end checks against the packaged command, not against the modules.
#
# Run it with the project's interpreter:
#   PY=.venv/bin/python bash smoke.sh
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAILS=0

ok() {
    PASS=$((PASS + 1))
    printf 'ok   %s\n' "$1"
}

bad() {
    FAILS=$((FAILS + 1))
    printf 'FAIL %s\n' "$1"
}

check_equal() {
    if [ "$2" = "$3" ]; then
        ok "$1"
    else
        bad "$1 (expected '$2', got '$3')"
    fi
}

check_contains() {
    case "$3" in
        *"$2"*) ok "$1" ;;
        *) bad "$1 (missing '$2' in: ${3:0:160})" ;;
    esac
}

run() {
    OUT="$("$@" 2>&1)"
    STATUS=$?
}

FIXTURES="$(cd "$(dirname "$0")" && pwd)/fixtures"

# --- the command answers at all ---------------------------------------------
run "$PY" -m "$MODULE" --version
check_equal "version exits zero" 0 "$STATUS"
check_contains "version names the program" "$PROGRAM" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists merge" "merge" "$OUT"
check_contains "help lists explain" "explain" "$OUT"

# --- a clean merge ----------------------------------------------------------
run "$PY" -m "$MODULE" merge \
    --base "$FIXTURES/clean-base.txt" \
    --ours "$FIXTURES/clean-ours.txt" \
    --theirs "$FIXTURES/clean-theirs.txt"
check_equal "a clean merge exits zero" 0 "$STATUS"
check_contains "the version bump survived" "## 1.5.0" "$OUT"
check_contains "the appended bullet survived" "- webhooks" "$OUT"
check_contains "the summary reports no conflict" "0 conflict(s)" "$OUT"

# --- a conflicted merge -----------------------------------------------------
run "$PY" -m "$MODULE" merge --base "$FIXTURES/base.txt" --ours "$FIXTURES/ours.txt" --theirs "$FIXTURES/theirs.txt"
check_equal "a conflict exits one" 1 "$STATUS"
check_contains "the ours marker is written" "<<<<<<< ours" "$OUT"
check_contains "the theirs marker is written" ">>>>>>> theirs" "$OUT"
check_contains "the separator is written" "=======" "$OUT"
check_contains "ours kept its replicas change" "replicas: 4" "$OUT"
check_contains "theirs kept its image change" "image: checkout:1.5.0" "$OUT"
check_contains "the disputed level is present twice" "level: warn" "$OUT"

# --- json -------------------------------------------------------------------
run "$PY" -m "$MODULE" merge --base "$FIXTURES/base.txt" --ours "$FIXTURES/ours.txt" --theirs "$FIXTURES/theirs.txt" --json --quiet
check_equal "a conflicted json merge exits one" 1 "$STATUS"
run "$PY" -c "import json,sys; d=json.loads(sys.argv[1]); print(d['conflicts'], d['clean'])" "$OUT"
check_equal "the json payload counts one conflict" "1 False" "$OUT"

# --- --out ------------------------------------------------------------------
run "$PY" -m "$MODULE" merge --base "$FIXTURES/clean-base.txt" --ours "$FIXTURES/clean-ours.txt" --theirs "$FIXTURES/clean-theirs.txt" --out "$WORK/merged.txt"
check_equal "writing to a file exits zero" 0 "$STATUS"
check_contains "the file holds the merge" "## 1.5.0" "$(cat "$WORK/merged.txt")"

# --- labels and styles ------------------------------------------------------
run "$PY" -m "$MODULE" merge --base "$FIXTURES/base.txt" --ours "$FIXTURES/ours.txt" --theirs "$FIXTURES/theirs.txt" --labels mine,yours
check_equal "labelled merge exits one" 1 "$STATUS"
check_contains "the ours label is used" "<<<<<<< mine" "$OUT"
check_contains "the theirs label is used" ">>>>>>> yours" "$OUT"

run "$PY" -m "$MODULE" merge --base "$FIXTURES/base.txt" --ours "$FIXTURES/ours.txt" --theirs "$FIXTURES/theirs.txt" --style diff3
check_contains "diff3 keeps the base section" "||||||| base" "$OUT"

# --- refusals ---------------------------------------------------------------
run "$PY" -m "$MODULE" merge --base "$FIXTURES/base.txt" --ours "$FIXTURES/ours.txt" --theirs "$FIXTURES/theirs.txt" --style squash
check_equal "an unknown style is unusable" 2 "$STATUS"

run "$PY" -m "$MODULE" merge --base "$FIXTURES/base.txt" --ours "$FIXTURES/ours.txt" --theirs "$WORK/nope.txt"
check_equal "a missing file is unusable" 2 "$STATUS"
check_contains "the error names the file" "nope.txt" "$OUT"

run "$PY" -m "$MODULE" merge --base "$FIXTURES/base.txt" --ours "$FIXTURES/ours.txt" --theirs "$FIXTURES/theirs.txt" --labels only
check_equal "one label is unusable" 2 "$STATUS"
check_contains "the error explains the labels" "two names" "$OUT"

# --- explain ----------------------------------------------------------------
run "$PY" -m "$MODULE" explain --base "$FIXTURES/clean-base.txt" --ours "$FIXTURES/clean-ours.txt" --theirs "$FIXTURES/clean-theirs.txt"
check_equal "explain exits zero on a clean merge" 0 "$STATUS"
check_contains "explain names the chunks" "chunks" "$OUT"

run "$PY" -m "$MODULE" explain --base "$FIXTURES/base.txt" --ours "$FIXTURES/ours.txt" --theirs "$FIXTURES/theirs.txt"
check_equal "explain exits one on a conflict" 1 "$STATUS"
check_contains "explain names the conflict" "conflict" "$OUT"

# --- demo and selftest ------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "demo exits zero" 0 "$STATUS"
check_contains "demo holds every story" "stories      6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "selftest exits zero" 0 "$STATUS"
check_contains "selftest reports no failures" "0 failed" "$OUT"

# --- one more shape: identical files ----------------------------------------
run "$PY" -m "$MODULE" merge --base "$FIXTURES/base.txt" --ours "$FIXTURES/base.txt" --theirs "$FIXTURES/base.txt"
check_equal "merging a file with itself exits zero" 0 "$STATUS"
check_contains "and the result is the file" "service: checkout" "$OUT"

printf '\nsmoke: %d passed, %d failed\n' "$PASS" "$FAILS"
[ "$FAILS" -eq 0 ]
