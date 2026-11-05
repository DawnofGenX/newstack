#!/usr/bin/env bash
# The shell contract: exit codes, the values on stdout, and nothing leaked.
#
# Run with the project virtualenv:
#   PY=.venv/bin/python bash smoke.sh
set -uo pipefail

PY="${PY:-python}"
cd "$(dirname "$0")" || exit 2

checks=0
failures=0
ok() { checks=$((checks + 1)); printf 'ok   %s\n' "$1"; }
fail() {
  checks=$((checks + 1))
  failures=$((failures + 1))
  printf 'FAIL %s\n' "$1"
  [ -n "${2:-}" ] && printf '     %s\n' "$2"
  return 0
}
expect() {
  if [ "$2" = "$3" ]; then ok "$1"; else fail "$1" "want [$2], got [$3]"; fi
}
contains() {
  case "$3" in
    *"$2"*) ok "$1" ;;
    *) fail "$1" "missing [$2] in: $3" ;;
  esac
}
lacks() {
  case "$3" in
    *"$2"*) fail "$1" "found [$2] in: $3" ;;
    *) ok "$1" ;;
  esac
}

# Nothing from the developer's own shell may leak into these checks.
for name in ${!APP_@}; do unset "$name"; done
OUT=""
STATUS=0
run() { OUT=$("$@" 2>&1); STATUS=$?; }

run "$PY" -m {{ package_name }} --version
expect "--version exits 0" 0 "$STATUS"
contains "--version names the program" "{{ npm_name }}" "$OUT"

run "$PY" -m {{ package_name }} selftest
expect "selftest exits 0" 0 "$STATUS"
contains "selftest reports no failures" "0 failed" "$OUT"

export APP_AUTH__SIGNING_KEY="smoke-signing-key"

run "$PY" -m {{ package_name }} check
expect "a complete configuration exits 0" 0 "$STATUS"
contains "check counts the settings" "check  ok: 10 settings" "$OUT"

run "$PY" -m {{ package_name }} check --strict
expect "--strict gates a shipped secret" 1 "$STATUS"
contains "the gate names the secret" "db.url is still the schema default" "$OUT"

export APP_DB__URL="postgres://localhost/app"
run "$PY" -m {{ package_name }} check --strict
expect "--strict passes once the secret is supplied" 0 "$STATUS"
contains "the gate says so" "gate   no secret is at its default" "$OUT"
unset APP_DB__URL

run "$PY" -m {{ package_name }} show
expect "show exits 0" 0 "$STATUS"
lacks "a secret is masked" "smoke-signing-key" "$OUT"
contains "the mask is visible" "***" "$OUT"

run "$PY" -m {{ package_name }} get auth.signing_key
expect "get refuses a secret" 2 "$STATUS"
contains "and says how to see it" "--reveal" "$OUT"

run "$PY" -m {{ package_name }} get auth.signing_key --reveal
expect "get --reveal prints it" 0 "$STATUS"
expect "the value is exact" "smoke-signing-key" "$OUT"

run "$PY" -m {{ package_name }} get server.port --config fixtures/config.toml
expect "a file value wins over the schema" 0 "$STATUS"
expect "the file port is 9100" "9100" "$OUT"

export APP_SERVER__PORT="9200"
run "$PY" -m {{ package_name }} get server.port --config fixtures/config.toml
expect "the environment wins over the file" 0 "$STATUS"
expect "the env port is 9200" "9200" "$OUT"

run "$PY" -m {{ package_name }} get server.port --config fixtures/config.toml \
  --set server.port=9300
expect "a flag wins over everything" 0 "$STATUS"
expect "the flag port is 9300" "9300" "$OUT"
unset APP_SERVER__PORT

run "$PY" -m {{ package_name }} show --config fixtures/config.toml --changed --json
expect "show --json exits 0" 0 "$STATUS"
contains "json says the file won" '"source": "file"' "$OUT"
contains "json carries the origin" 'fixtures/config.toml' "$OUT"

run "$PY" -m {{ package_name }} get server.timeout --config fixtures/config.toml
expect "a duration is rendered in milliseconds" 0 "$STATUS"
expect "2500ms became 2500" "2500" "$OUT"

run "$PY" -m {{ package_name }} check --config fixtures/broken.toml
expect "a broken file is exit 2" 2 "$STATUS"
contains "the range is enforced" "70000 is above the maximum" "$OUT"
contains "the typo is named" "tymeout" "$OUT"
contains "the bad choice is named" "verbose" "$OUT"

APP_SERVER_PORT="9200" run "$PY" -m {{ package_name }} check
expect "a single-underscore variable is exit 2" 2 "$STATUS"
contains "and the hint is a double underscore" "double underscore" "$OUT"

APP_SERVER__TIMEOUT="" run "$PY" -m {{ package_name }} check
expect "an empty variable is not an unset one" 2 "$STATUS"
contains "and the message quotes it" "expected a duration" "$OUT"

run "$PY" -m {{ package_name }} check --set server.port=abc
expect "a bad flag value is exit 2" 2 "$STATUS"
contains "and the message says integer" "expected an integer" "$OUT"

run "$PY" -m {{ package_name }} check --config fixtures/absent.toml
expect "a missing file is exit 2" 2 "$STATUS"
contains "and the message says so" "cannot read" "$OUT"

printf '\n%d checks, %d failed\n' "$checks" "$failures"
if [ "$failures" -ne 0 ]; then
  printf 'smoke: FAILED\n'
  exit 1
fi
printf 'smoke: all checks passed\n'
