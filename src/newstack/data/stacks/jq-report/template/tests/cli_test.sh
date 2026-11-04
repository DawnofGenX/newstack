#!/usr/bin/env bash
# The command surface: what is listed, what is refused, and which exit status
# each mistake gets. These numbers are the tool's contract.

suite_cli() {
  run_capture "$BIN" filters
  check "filters exits 0" 0 "$STATUS"
  check "filters lists the five filters in order" \
    "bytes-by-day
error-rate
slowest
status-counts
top-paths" "$OUT"

  run_capture "$BIN" help
  check "help exits 0" 0 "$STATUS"
  check_contains "help names the program" "Usage: $PROG COMMAND [ARG]..." "$OUT"
  check_contains "help documents run" "run FILTER [FILE]" "$OUT"
  check_contains "help documents the exit codes" "2  usage error" "$OUT"
  run_capture "$BIN" --help
  check "--help exits 0" 0 "$STATUS"
  check "--help prints the same text as help" "$OUT" "$("$BIN" help)"

  run_capture "$BIN"
  check "no command is a usage error" 2 "$STATUS"
  check_contains "no command explains itself" "no command given" "$ERR"

  run_capture "$BIN" --bogus
  check "an unknown option is a usage error" 2 "$STATUS"
  check_contains "an unknown option is named" "unknown option: --bogus" "$ERR"

  run_capture "$BIN" frobnicate
  check "an unknown command is a usage error" 2 "$STATUS"
  check_contains "an unknown command is named" "unknown command: frobnicate" "$ERR"

  run_capture "$BIN" run
  check "run without a filter is a usage error" 2 "$STATUS"
  check_contains "run without a filter says what is missing" "run needs a filter name" "$ERR"

  run_capture "$BIN" run nope "$DATA"
  check "an unknown filter is a usage error" 2 "$STATUS"
  check_contains "an unknown filter is named" "no such filter: nope" "$ERR"

  run_capture "$BIN" run status-counts "$DATA" extra
  check "a third argument is a usage error" 2 "$STATUS"

  run_capture "$BIN" filters extra
  check "filters takes no arguments" 2 "$STATUS"

  run_capture "$BIN" run status-counts /nonexistent/log.json
  check "a missing file is a data error" 1 "$STATUS"
  check_contains "a missing file is named" "cannot read /nonexistent/log.json" "$ERR"

  printf 'this is not json\n' >"$TMP/bad.json"
  run_capture "$BIN" run status-counts "$TMP/bad.json"
  check "malformed JSON is a data error" 1 "$STATUS"
  check_contains "malformed JSON is explained" "is not valid JSON" "$ERR"

  # The same log through a file and through stdin must be indistinguishable.
  local from_file from_stdin from_dash
  run_capture "$BIN" run slowest "$DATA"
  from_file=$OUT
  from_stdin=$(cd "$ROOT" && "$BIN" run slowest <"$DATA" 2>"$ERRFILE")
  check "stdin is the default input" "$from_file" "$from_stdin"
  from_dash=$(cd "$ROOT" && "$BIN" run slowest - <"$DATA" 2>"$ERRFILE")
  check "an explicit dash means stdin" "$from_file" "$from_dash"

  # The wrapper finds the project from any directory.
  check "a relative path works from the project root" 0 \
    "$(cd "$ROOT" && "$BIN" run slowest data/sample.json >/dev/null 2>&1; echo $?)"
  check "the wrapper works from elsewhere" 0 \
    "$(cd "$TMP" && "$BIN" run status-counts "$DATA" >/dev/null 2>&1; echo $?)"

  run_capture "$BIN" lint
  check "lint exits 0 when every filter compiles" 0 "$STATUS"
  check "lint prints one line per filter" 5 "$(printf '%s\n' "$OUT" | grep -c '')"
  check_contains "lint reports the filters it checked" "ok   error-rate.jq" "$OUT"

  mkdir -p "$TMP/broken"
  printf 'group_by(.status\n' >"$TMP/broken/broken.jq"
  run_capture "$BIN" lint "$TMP/broken"
  check "lint fails on a filter that does not compile" 1 "$STATUS"
  check_contains "lint names the broken filter" "broken.jq does not compile" "$ERR"

  run_capture "$BIN" lint "$TMP/nowhere"
  check "lint on a missing directory is a usage error" 2 "$STATUS"

  # A filter that compiles but blows up on the data is a data error (exit 1),
  # not a stack trace and not a usage error. This one is added to a copy of the
  # project so the shipped filters stay untouched.
  cp -r "$ROOT" "$TMP/project"
  printf '. as $x | $x.deep.deeper\n' >"$TMP/project/filters/deep.jq"
  run_capture "$TMP/project/bin/$PROG" lint
  check "a filter that compiles but cannot run still lints" 0 "$STATUS"
  run_capture "$TMP/project/bin/$PROG" run deep "$DATA"
  check "a filter that fails on the data is a data error" 1 "$STATUS"
  check_contains "the runtime failure is reported" "$PROG: error" "$ERR"
}
