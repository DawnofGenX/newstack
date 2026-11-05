#!/usr/bin/env bash
# Two servers on two ports: one obeys the document, the other has drifted from it.
# Every check below is something a caller would otherwise have to notice by hand.
set -euo pipefail

PY=${PY:-python}
PORT=${PORT:-5473}
DRIFT_PORT=${DRIFT_PORT:-5474}
CLI=("$PY" -m {{ package_name }})
tmp=$(mktemp -d)
honest_pid=""
drift_pid=""

cleanup() {
  status=$?
  [ -n "$honest_pid" ] && kill "$honest_pid" 2>/dev/null || true
  [ -n "$drift_pid" ] && kill "$drift_pid" 2>/dev/null || true
  rm -rf "$tmp"
  exit $status
}
trap cleanup EXIT

check() {
  local label=$1; shift
  if "$@" >/dev/null 2>&1; then
    echo "  ok   $label"
  else
    echo "  FAIL $label" >&2
    exit 1
  fi
}

echo "smoke: notes API on $PORT (honest) and $DRIFT_PORT (drifted)"

if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
  echo "smoke: port $PORT is already in use" >&2
  exit 1
fi
if ss -ltn 2>/dev/null | grep -q ":$DRIFT_PORT "; then
  echo "smoke: port $DRIFT_PORT is already in use" >&2
  exit 1
fi

"$PY" fixtures/server.py --port "$PORT" >"$tmp/honest.log" 2>&1 &
honest_pid=$!
"$PY" fixtures/server.py --port "$DRIFT_PORT" --drift >"$tmp/drift.log" 2>&1 &
drift_pid=$!
for _ in $(seq 1 50); do
  ss -ltn 2>/dev/null | grep -q ":$PORT " && break
  sleep 0.1
done

BASE="http://127.0.0.1:$PORT"
DRIFTED="http://127.0.0.1:$DRIFT_PORT"

# 1. the document is readable and every operation is named
"${CLI[@]}" --spec fixtures/openapi.json --base-url "$BASE" list >"$tmp/list.txt"
grep -q "listNotes" "$tmp/list.txt"
grep -q "createNote" "$tmp/list.txt"
grep -q "getNote" "$tmp/list.txt"
echo "  ok   list names all three operations"

# 2. a conforming call fits and prints its status
"${CLI[@]}" --base-url "$BASE" call listNotes >"$tmp/list.json"
grep -q "^200 listNotes" "$tmp/list.json"
grep -q '"title": "first"' "$tmp/list.json"
echo "  ok   a conforming response is accepted"

# 3. parameters reach the query string
"${CLI[@]}" --base-url "$BASE" call listNotes --param limit=2 >"$tmp/limited.json"
grep -q "limit=2" "$tmp/limited.json"
echo "  ok   a query parameter reaches the request"

# 4. a request body is sent, and the 201 is checked
printf '{"title": "from smoke", "tags": ["smoke"]}' >"$tmp/request.json"
"${CLI[@]}" --base-url "$BASE" call createNote --body "$tmp/request.json" >"$tmp/created.json"
grep -q "^201 createNote" "$tmp/created.json"
grep -q '"title": "from smoke"' "$tmp/created.json"
echo "  ok   a documented 201 is accepted"

# 5. a path value is percent-encoded, so a slash cannot invent a path segment
"${CLI[@]}" --base-url "$BASE" call getNote --param id=a/b --json >"$tmp/encoded.json"
grep -q '"detail": "a%2Fb"' "$tmp/encoded.json"
echo "  ok   a slash in a path value is encoded, not routed"

# 6. a documented 404 with a body is a valid answer, not a failure
"${CLI[@]}" --base-url "$BASE" call getNote --param id=999 >/dev/null
echo "  ok   a documented 404 is not drift"

# 7. the drifted server is caught, with the member named
set +e
"${CLI[@]}" --base-url "$DRIFTED" call listNotes >"$tmp/drift.out" 2>"$tmp/drift.err"
drift_status=$?
set -e
test "$drift_status" -eq 1
grep -q '\[0\]\.tags: expected array, got integer' "$tmp/drift.err"
grep -q "unexpected member 'server_side'" "$tmp/drift.err"
echo "  ok   drift exits 1 and names the member"

# 8. offline checking of a saved response, both ways
printf '{"id": "1", "title": "first", "tags": [], "pinned": false}' >"$tmp/good.json"
"${CLI[@]}" validate --operation getNote --response "$tmp/good.json" >/dev/null
printf '{"id": 1, "title": "first", "tags": [], "pinned": false}' >"$tmp/bad.json"
set +e
"${CLI[@]}" validate --operation getNote --response "$tmp/bad.json" >/dev/null 2>&1
bad_status=$?
set -e
test "$bad_status" -eq 1
echo "  ok   validate checks a saved response both ways"

# 9. the tool's own refusals, each with a distinct exit code
set +e
"${CLI[@]}" --base-url "$BASE" call deleteNote >/dev/null 2>&1;   unknown=$?
"${CLI[@]}" --base-url "$BASE" call getNote >/dev/null 2>&1;      missing=$?
"${CLI[@]}" --base-url "$BASE" call listNotes --param p9=1 >/dev/null 2>&1; bogus=$?
"${CLI[@]}" --base-url http://127.0.0.1:5999 call listNotes >/dev/null 2>&1; dead=$?
set -e
test "$unknown" -eq 2
test "$missing" -eq 2
test "$bogus" -eq 2
test "$dead" -eq 2
echo "  ok   unknown operation, missing parameter, undeclared parameter and a dead server all exit 2"

# 10. the checker checks itself, against two live servers
"${CLI[@]}" selftest >"$tmp/selftest.txt"
grep -q "selftest: .* checks passed" "$tmp/selftest.txt"
echo "  ok   selftest passes"

# 11. a request that breaks the document never leaves the process
set +e
"${CLI[@]}" --base-url "$BASE" call createNote --body <(printf '{"tags": []}') >/dev/null 2>"$tmp/req.err"
req_status=$?
set -e
test "$req_status" -eq 1
grep -q "missing required member 'title'" "$tmp/req.err"
echo "  ok   an invalid request is refused before it is sent"

echo "smoke: all checks passed"
