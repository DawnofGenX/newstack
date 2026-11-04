#!/usr/bin/env bash
# A very small assertion harness: no framework, no downloads, no plugins.
# Every check prints nothing when it passes; failures collect at the end so one
# broken filter does not hide the next twenty.

PASS=0
FAIL=0
FAILED=()

check() { # label want got
  if [ "$2" = "$3" ]; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
    FAILED+=("$1: want [$2] got [$3]")
  fi
}

check_contains() { # label needle haystack
  case $3 in
    *"$2"*) PASS=$((PASS + 1)) ;;
    *)
      FAIL=$((FAIL + 1))
      FAILED+=("$1: [$3] does not contain [$2]")
      ;;
  esac
}

run_capture() { # args...
  OUT=$("$@" 2>"$ERRFILE")
  STATUS=$?
  ERR=$(cat "$ERRFILE")
}

report() {
  local failure
  for failure in "${FAILED[@]:-}"; do
    [ -n "$failure" ] && printf 'not ok  %s\n' "$failure" >&2
  done
  printf 'checks: %d, passed: %d, failed: %d\n' "$((PASS + FAIL))" "$PASS" "$FAIL"
  [ "$FAIL" -eq 0 ]
}
