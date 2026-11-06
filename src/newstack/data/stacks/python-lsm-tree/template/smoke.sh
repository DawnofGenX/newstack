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

# --- write, read, tombstone ---------------------------------------------------
run "$PY" -m "$MODULE" put --dir "$WORK/t" --key 12 --value alpha
check_equal "a put exits zero" 0 "$STATUS"
check_contains "the put names the value" "alpha" "$OUT"

run "$PY" -m "$MODULE" get --dir "$WORK/t" --key 12
check_equal "a held key exits zero" 0 "$STATUS"
check_contains "the held value comes back" "alpha" "$OUT"

run "$PY" -m "$MODULE" get --dir "$WORK/t" --key 99
check_equal "an unknown key exits one" 1 "$STATUS"

run "$PY" -m "$MODULE" delete --dir "$WORK/t" --key 12
check_equal "a delete exits zero" 0 "$STATUS"

run "$PY" -m "$MODULE" get --dir "$WORK/t" --key 12
check_equal "the tombstone hides the value" 1 "$STATUS"

run "$PY" -m "$MODULE" get --dir "$WORK/missing/dir" --key 1
check_equal "an empty directory answers absent" 1 "$STATUS"

# --- levels, tombstones, and the fall-through ----------------------------------
run "$PY" -m "$MODULE" put --dir "$WORK/f" --key 7 --value first
check_equal "a put freezes its level" 0 "$STATUS"
check_contains "the put names its level" "flushed    0" "$OUT"

run "$PY" -m "$MODULE" flush --dir "$WORK/f"
check_equal "a flush of nothing adds no level" 1 "$STATUS"

run "$PY" -m "$MODULE" delete --dir "$WORK/f" --key 7
check_equal "a delete freezes its tombstone" 0 "$STATUS"
run "$PY" -m "$MODULE" get --dir "$WORK/f" --key 7
check_equal "the tombstone outranks the frozen value" 1 "$STATUS"

run "$PY" -m "$MODULE" put --dir "$WORK/f" --key 7 --value second
check_equal "a re-put outranks the tombstone" 0 "$STATUS"
run "$PY" -m "$MODULE" get --dir "$WORK/f" --key 7 --json
READ=$(
  "$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["value"])' "$OUT"
)
check_equal "the newest level answers first" "second" "$READ"

# --- compaction ------------------------------------------------------------------
run "$PY" -m "$MODULE" compact --dir "$WORK/f"
check_equal "a merge exits zero" 0 "$STATUS"
check_contains "the merge reports one table" "merged into 1" "$OUT"
run "$PY" -m "$MODULE" get --dir "$WORK/f" --key 7
check_equal "the answer survives the merge" 0 "$STATUS"

# --- the seeded workload ------------------------------------------------------------
run "$PY" -m "$MODULE" workload --dir "$WORK/w" --seed 7 --limit 3
check_equal "the workload agrees with the dict" 0 "$STATUS"
check_contains "the agreement is stated" "agreed     True" "$OUT"
check_equal "a second seed agrees too" "True" "$(
  "$PY" -m "$MODULE" workload --dir "$WORK/w2" --seed 23 --limit 1 --json \
    | "$PY" -c 'import json,sys; print(json.loads(sys.stdin.read())["agreed"])'
)"

run "$PY" -m "$MODULE" workload --dir "$WORK/w3" --seed 7 --limit 0
check_equal "a zero limit is unusable" 2 "$STATUS"

# --- the fixture replay ------------------------------------------------------------------
run "$PY" -m "$MODULE" load --dir "$WORK/fixture" --ops fixtures/ops.txt
check_equal "the fixture replays" 0 "$STATUS"
check_contains "the fixture reaches the levels" "levels" "$OUT"

# --- the stories ------------------------------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo stories hold" 0 "$STATUS"
check_contains "the dict story ships" "answers exactly what the dict answers" "$OUT"

# --- the invariants ------------------------------------------------------------------------------
run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]
