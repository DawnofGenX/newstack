#!/usr/bin/env bash
# Smoke test: run every command the README promises, on the fixture ignore file.
#
#   PY=.venv/bin/python bash smoke.sh
#
# Uses its own scratch directory under $TMPDIR, so it never touches the project.

set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
IGNORE="fixtures/.gitignore"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/gitignore-smoke.XXXXXX")"
PASSED=0
FAILED=0

cleanup() {
  rm -rf "$WORK"
}
trap cleanup EXIT

ok() {
  PASSED=$((PASSED + 1))
  echo "ok   $1"
}

bad() {
  FAILED=$((FAILED + 1))
  echo "FAIL $1${2:+: $2}"
}

check() {
  local name="$1" condition="$2" detail="${3:-}"
  if [ "$condition" = "1" ]; then ok "$name"; else bad "$name" "$detail"; fi
}

check_equal() {
  local name="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    ok "$name"
  else
    bad "$name" "expected '$expected', got '$actual'"
  fi
}

check_contains() {
  local name="$1" needle="$2" haystack="$3"
  case "$haystack" in
    *"$needle"*) ok "$name" ;;
    *) bad "$name" "missing '$needle' in: $haystack" ;;
  esac
}

OUT=""
STATUS=0

run() {
  OUT=$("$@" 2>&1)
  STATUS=$?
}

mod() {
  "$PY" -m "$MODULE" "$@"
}

# --- version and help -------------------------------------------------------
run mod --version
check_equal "version exits zero" "0" "$STATUS"
check_contains "version names the program" "$PROGRAM" "$OUT"

run mod --help
check_equal "help exits zero" "0" "$STATUS"
check_contains "help lists explain" "explain" "$OUT"

# --- the demo ---------------------------------------------------------------
run mod demo
check_equal "demo exits zero" "0" "$STATUS"
check_contains "demo counts its stories" "stories      6 of 6 hold" "$OUT"

# --- reading the fixture ----------------------------------------------------
run mod list --ignore "$IGNORE"
check_equal "list exits zero" "0" "$STATUS"
check_contains "list shows the negation" "!release.log" "$OUT"
check_contains "list flags a directory rule" "directory only" "$OUT"
check_contains "list flags an anchored rule" "anchored" "$OUT"

run mod list --ignore "$IGNORE" --json
check_equal "list --json exits zero" "0" "$STATUS"
RULES=$(printf '%s' "$OUT" | "$PY" -c 'import json,sys; print(len(json.load(sys.stdin)))')
check_equal "every rule is reported" "14" "$RULES"

# --- explain: the ordinary cases -------------------------------------------
run mod explain app.log --ignore "$IGNORE"
check_equal "an ignored path exits one" "1" "$STATUS"
check_contains "the verdict says ignored" "verdict    ignored" "$OUT"
check_contains "the deciding line is named" "line 12: *.log" "$OUT"

run mod explain src/app.py --ignore "$IGNORE"
check_equal "a tracked path exits zero" "0" "$STATUS"
check_contains "the verdict says not ignored" "verdict    not ignored" "$OUT"

run mod explain release.log --ignore "$IGNORE"
check_equal "a negation drives the exit code" "0" "$STATUS"
check_contains "the negation is the deciding rule" "!release.log" "$OUT"

run mod explain .env --ignore "$IGNORE"
check_equal "a dotfile can be ignored" "1" "$STATUS"

run mod explain env.example --ignore "$IGNORE"
check_equal "a negation rescues an example file" "0" "$STATUS"

# --- explain: anchoring, directories, ancestors -----------------------------
run mod explain build
check_equal "a file named build is tracked" "0" "$STATUS"

run mod explain build/out/app.js --ignore "$IGNORE"
check_equal "a file under an ignored directory is ignored" "1" "$STATUS"
check_contains "the parent is named" "its parent 'build'" "$OUT"

run mod explain src/__pycache__ --directory --ignore "$IGNORE"
check_equal "a bare directory rule matches at depth" "1" "$STATUS"

run mod explain src/__pycache__/app.cpython-313.pyc --ignore "$IGNORE"
check_equal "bytecode under a cache directory is ignored" "1" "$STATUS"

run mod explain fixtures/data.json --ignore "$IGNORE"
check_equal "the fixture negation wins by being last" "0" "$STATUS"

run mod explain logs/2026/11/deep.log --ignore "$IGNORE"
check_equal "a bare name rule reaches any depth" "1" "$STATUS"

# --- json -------------------------------------------------------------------
run mod explain app.log --ignore "$IGNORE" --json
check_equal "explain --json still exits one" "1" "$STATUS"
JSON_OK=$(printf '%s' "$OUT" | "$PY" -c '
import json, sys
payload = json.load(sys.stdin)
print("yes" if payload["ignored"] is True and payload["line"] == 12 else "no")
')
check_equal "the json verdict carries the rule number" "yes" "$JSON_OK"

# --- order matters ----------------------------------------------------------
printf '!keep.log\n*.log\n' > "$WORK/reversed"
run mod explain keep.log --ignore "$WORK/reversed"
check_equal "a later general rule beats an earlier negation" "1" "$STATUS"

# --- walk -------------------------------------------------------------------
mkdir -p "$WORK/tree/build/sub" "$WORK/tree/src"
printf 'x' > "$WORK/tree/build/sub/app.js"
printf 'x' > "$WORK/tree/src/main.py"
printf 'x' > "$WORK/tree/app.log"
printf '*.log\nbuild/\n' > "$WORK/tree/.gitignore"
run mod walk "$WORK/tree" --ignore "$WORK/tree/.gitignore" --json
check_equal "walk exits zero" "0" "$STATUS"
COUNTS=$(printf '%s' "$OUT" | "$PY" -c '
import json, sys
payload = json.load(sys.stdin)
print(payload["paths"], payload["ignored"])
')
check_equal "the walk counts both kinds" "7 4" "$COUNTS"

# --- refusals ---------------------------------------------------------------
run mod explain app.log --ignore "$WORK/absent"
check_equal "a missing ignore file is unusable" "2" "$STATUS"
check_contains "the message names the file" "no such ignore file" "$OUT"

run mod explain ../outside --ignore "$IGNORE"
check_equal "a path outside the tree is unusable" "2" "$STATUS"
check_contains "the message explains why" "steps outside the tree" "$OUT"

printf 'file[0-9\n' > "$WORK/broken"
run mod explain app.log --ignore "$WORK/broken"
check_equal "an unclosed class is unusable" "2" "$STATUS"
check_contains "the message quotes the line" "never closes it" "$OUT"

printf '# only a comment\n' > "$WORK/empty"
run mod explain app.log --ignore "$WORK/empty"
check_equal "an empty rule set is unusable" "2" "$STATUS"

# --- selftest ---------------------------------------------------------------
run mod selftest
check_equal "selftest exits zero" "0" "$STATUS"
check_contains "selftest reports no failures" "0 failed" "$OUT"

echo
echo "smoke: $PASSED passed, $FAILED failed"
if [ "$FAILED" -ne 0 ]; then
  exit 1
fi
