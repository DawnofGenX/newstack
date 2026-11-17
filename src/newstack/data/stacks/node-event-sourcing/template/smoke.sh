#!/usr/bin/env bash
# The contract is exit codes and what the log looks like afterwards.
#
# Deliberately not `set -e`: a smoke test that dies on the first failure reports
# one symptom instead of the whole list.
set -uo pipefail

cd "$(dirname "$0")"
NODE="${NODE:-node}"
ENTRY="dist/src/main.js"
# The banner prints the npm name, which the scaffold decides; read it instead of
# assuming it, or this check passes only at the name it was written at.
PROGRAM=$("$NODE" -p 'require("./package.json").name')

if [ ! -f "$ENTRY" ]; then
  echo "smoke: build first (npm run build)" >&2
  exit 1
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
failures=0
LOG="$work/events.jsonl"
CHECKPOINT="$work/accounts.checkpoint"

check() {
  local name="$1" status="$2"
  if [ "$status" -eq 0 ]; then
    printf 'ok   %s\n' "$name"
  else
    printf 'FAIL %s\n' "$name"
    failures=$((failures + 1))
  fi
}

check_contains() {
  local name="$1" haystack="$2" needle="$3"
  case "$haystack" in
    *"$needle"*) check "$name" 0 ;;
    *) check "$name" 1; printf '     wanted: %s\n     got:    %s\n' "$needle" "$haystack" ;;
  esac
}

run() { "$NODE" "$ENTRY" "$@" 2>&1; }

out=$(run --version)
check_contains "the version banner names the program" "$out" "$PROGRAM "

out=$(run append --log "$LOG" --stream acct --expected-version 0 --type deposited --data '{"amount":100}')
check "a first append exits 0" $?
check_contains "the append prints its global position" "$out" "#0  acct v1"
check_contains "the append prints the payload" "$out" '{"amount":100}'

out=$(run append --log "$LOG" --stream acct --expected-version 1 \
  --type withdrawn --data '{"amount":30}' --type deposited --data '{"amount":5}')
check "a batch append exits 0" $?
check_contains "the batch numbers both events" "$out" "#2  acct v3"

lines=$(wc -l < "$LOG" | tr -d ' ')
check "one append is one line in the log" "$([ "$lines" -eq 2 ] && echo 0 || echo 1)"

out=$(run read --log "$LOG")
check_contains "read counts the events" "$out" "3 event(s), position 3"

out=$(run read --log "$LOG" --from 2)
check_contains "read can start at a position" "$out" "1 event(s)"

out=$(run append --log "$LOG" --stream acct --expected-version 1 --type deposited --data '{"amount":1}')
status=$?
check "a stale append exits 1" "$([ "$status" -eq 1 ] && echo 0 || echo 1)"
check_contains "the refusal names both versions" "$out" "version 3, not 1"
check_contains "the refusal says what to do" "$out" "re-reading before retrying"

out=$(run read --log "$LOG")
check_contains "the refused append left the log alone" "$out" "3 event(s)"

out=$(run append --log "$LOG" --stream acct --expected-version 3 --type deposited --data '{oops')
status=$?
check "malformed json exits 2" "$([ "$status" -eq 2 ] && echo 0 || echo 1)"
check_contains "malformed json says which flag" "$out" "--data is not valid JSON"

out=$(run append --log "$LOG" --stream acct --expected-version 3 --type deposited)
status=$?
check "an append without data exits 2" "$([ "$status" -eq 2 ] && echo 0 || echo 1)"

out=$(run nope)
status=$?
check "an unknown command exits 2" "$([ "$status" -eq 2 ] && echo 0 || echo 1)"
check_contains "an unknown command names itself" "$out" "unknown command nope"

out=$(run --help)
check "help exits 0" $?
check_contains "help lists the commands" "$out" "append   --log PATH"

out=$(run project --log "$LOG" --checkpoint "$CHECKPOINT")
check_contains "the first projection folds from zero" "$out" "checkpoint  0 -> 3"
check_contains "the projected balance is right" "$out" "balance     75"
check_contains "the replay matches a rebuild" "$out" "matches a full rebuild"

out=$(run project --log "$LOG" --checkpoint "$CHECKPOINT")
check_contains "a second projection resumes at the head" "$out" "resumed at  3 (saved state)"
check_contains "a second projection applies nothing" "$out" "applied     0 event(s), 3 already folded in"

out=$("$NODE" -e '
  const { readFileSync } = require("node:fs");
  const payload = JSON.parse(readFileSync(process.argv[1], "utf8"));
  console.log(payload.position, payload.state.balance);
' "$CHECKPOINT")
check_contains "the checkpoint keeps its position and state" "$out" "3 75"

out=$(run demo)
check "the demo exits 0" $?
check_contains "the demo proves the fold is replayable" "$out" "yes: the fold is replayable"
check_contains "the demo refuses a stale append" "$out" "another writer appended first"

# A crash mid-write leaves a partial line. The loader must drop exactly that one.
printf '{"stream":"acct","fromVers' >> "$LOG"
out=$("$NODE" --input-type=module -e '
  const { EventStore } = await import("./dist/src/store.js");
  const store = EventStore.open(process.argv[1]);
  console.log(`position=${store.position} dropped=${store.dropped} version=${store.version("acct")}`);
' "$LOG")
check_contains "a torn final line is dropped and counted" "$out" "position=3 dropped=1 version=3"

out=$(run read --log "$LOG")
check_contains "the log is still readable after a crash" "$out" "3 event(s)"

if [ "$failures" -eq 0 ]; then
  printf 'smoke: all checks passed\n'
  exit 0
fi
printf 'smoke: %d check(s) failed\n' "$failures"
exit 1
