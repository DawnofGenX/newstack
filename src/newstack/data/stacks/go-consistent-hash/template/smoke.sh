#!/usr/bin/env bash
set -euo pipefail

# smoke.sh — end-to-end contract check against a live {{ npm_name }} on :$PORT
PORT="${PORT:-5490}"
BASE="http://127.0.0.1:${PORT}"
BIN="./build/{{ npm_name }}"
CHECKS=0
FAILED=0
SERVER_PID=""

check() { # check <label> <expected> <actual>
  CHECKS=$((CHECKS + 1))
  if [[ "$2" == "$3" ]]; then
    return 0
  fi
  FAILED=$((FAILED + 1))
  printf '  FAIL: %s\n    want: %s\n    got:  %s\n' "$1" "$2" "$3" >&2
}

contains() { # contains <label> <needle> <haystack>
  CHECKS=$((CHECKS + 1))
  if [[ "$3" == *"$2"* ]]; then
    return 0
  fi
  FAILED=$((FAILED + 1))
  printf '  FAIL: %s\n    missing: %s\n    in:      %s\n' "$1" "$2" "$3" >&2
}

cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill -TERM "${SERVER_PID}" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "${SERVER_PID}" 2>/dev/null || break
      sleep 0.1
    done
    kill -KILL "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# --- pre-flight: port must be free ---
if curl -fsS -m 2 "${BASE}/health" >/dev/null 2>&1; then
  echo "port ${PORT} is already answering - stop that process before running this step" >&2
  exit 1
fi

[[ -x "${BIN}" ]] || { echo "missing ${BIN}; run make build" >&2; exit 1; }

PORT="${PORT}" "${BIN}" >server.log 2>&1 &
SERVER_PID=$!

# --- readiness: 160 x 0.25s ---
ready=0
for _ in $(seq 1 160); do
  if curl -fsS -m 1 "${BASE}/health" >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.25
done
if [[ "${ready}" != 1 ]]; then
  echo "server did not become ready; log:" >&2
  cat server.log >&2 || true
  exit 1
fi

# 1. health JSON shape
body="$(curl -fsS "${BASE}/health")"
contains "health is 3-node JSON" '"nodes":3,"replicas":2,"points":450,"keys":{' "${body}"

# 2. put / get / delete
put_body="$(curl -sS -w '\n%{http_code}' -X PUT -d 'smoke-value' "${BASE}/kv/smoke-key")"
code="${put_body##*$'\n'}"
put_body="${put_body%$'\n'*}"
check "PUT smoke-key" "200" "${code}"
val="$(curl -sS "${BASE}/kv/smoke-key")"
put_owners="${put_body#*\"owners\":}"
put_owners="${put_owners%%]*}"
put_commas="$(printf '%s' "${put_owners}" | tr -cd ',' | wc -c)"
check "PUT reports two replica owners" "1" "${put_commas}"
check "GET smoke-key" "smoke-value" "${val}"
code="$(curl -sS -o /dev/null -w '%{http_code}' -X DELETE "${BASE}/kv/smoke-key")"
check "DELETE smoke-key" "204" "${code}"

# 3. 404 body names the key
body="$(curl -sS "${BASE}/kv/ghost")"
contains "404 body has error" '"error":"not_found"' "${body}"
contains "404 body names key" '"key":"ghost"' "${body}"

# 4. 405 on wrong method
code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST "${BASE}/health")"
check "POST /health" "405" "${code}"
body="$(curl -sS -X POST "${BASE}/health")"
contains "405 body" '"error":"method_not_allowed"' "${body}"

# 5. 413 on 70 KiB body
python3 -c 'print("x"*71680, end="")' >big.value 2>/dev/null || printf 'x%.0s' $(seq 1 71680) >big.value
code="$(curl -sS -o /dev/null -w '%{http_code}' -X PUT --data-binary @big.value "${BASE}/kv/big")"
check "PUT 70KiB" "413" "${code}"

# 6. ring owners for key=abc
body="$(curl -sS "${BASE}/_ring?key=abc")"
contains "ring owners for abc" '"key":"abc"' "${body}"
contains "ring owners non-empty" '"owners":["' "${body}"
owners="${body#*\"owners\":}"
owners="${owners%%]*}"
commas="$(printf '%s' "${owners}" | tr -cd ',' | wc -c)"
check "replicas own two copies" "1" "${commas}"

# 7. remove a node -> ring points drop 450 -> 300
code="$(curl -sS -o /dev/null -w '%{http_code}' -X DELETE "${BASE}/_node/gamma")"
check "DELETE /_node/gamma" "200" "${code}"
body="$(curl -fsS "${BASE}/health")"
contains "points dropped to 300" '"points":300' "${body}"

# 8. a key still reads after removal
code="$(curl -sS -o /dev/null -w '%{http_code}' -X PUT -d 'persist' "${BASE}/kv/post-removal")"
check "PUT post-removal" "200" "${code}"
val="$(curl -sS "${BASE}/kv/post-removal")"
check "GET post-removal survives" "persist" "${val}"

rm -f big.value server.log

printf 'smoke: %d checks, %d failed\n' "${CHECKS}" "${FAILED}"
[[ "${FAILED}" -eq 0 ]] || exit 1
