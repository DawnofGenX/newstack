#!/usr/bin/env bash
# End-to-end checks against the shipped corpus and judgements.
#
# Run with the project virtualenv:
#   PY=.venv/bin/python bash smoke.sh
set -euo pipefail

PY="${PY:-python}"
cd "$(dirname "$0")"

failures=0
check() {
  local name="$1"
  local status="$2"
  if [ "$status" -eq 0 ]; then
    printf 'ok   %s\n' "$name"
  else
    printf 'FAIL %s\n' "$name"
    failures=$((failures + 1))
  fi
}

out=$("$PY" -m {{ package_name }} eval)
check "eval succeeds" $?
printf '%s\n' "$out" | grep -q '^macro  recall@3' ; check "macro recall is printed" $?
printf '%s\n' "$out" | grep -q '^micro  recall@3' ; check "micro recall is printed" $?
printf '%s\n' "$out" | grep -q 'skip   no judgements' ; check "an unjudged query is skipped" $?

"$PY" -m {{ package_name }} eval --k 1 | grep -q 'recall@1' ; check "k is selectable" $?

"$PY" -m {{ package_name }} eval --json > report.json
check "json report succeeds" $?
"$PY" - <<'PYCODE'
import json
payload = json.load(open("report.json", encoding="utf-8"))
assert payload["queries"] == 6, payload["queries"]
assert payload["skipped"] == 1, payload["skipped"]
assert payload["macro_recall"] >= 0.8, payload["macro_recall"]
assert len(payload["per_query"]) == 6
PYCODE
check "json report has the expected shape" $?

top=$("$PY" -m {{ package_name }} search "how do I rotate a signing key" --k 1)
printf '%s\n' "$top" | grep -q 'rotate-key.md' ; check "search finds the labelled document" $?

set +e
"$PY" -m {{ package_name }} search "zebra unicorn xylophone" >/dev/null 2>&1
status=$?
set -e
test "$status" -eq 1 ; check "a query with nothing in common exits 1" $?

"$PY" -m {{ package_name }} compare --baseline report.json --candidate report.json >/dev/null
check "compare against itself passes" $?

"$PY" - <<'PYCODE'
import json
payload = json.load(open("report.json", encoding="utf-8"))
payload["ndcg"] = payload["ndcg"] - 0.2
json.dump(payload, open("worse.json", "w", encoding="utf-8"))
PYCODE
set +e
"$PY" -m {{ package_name }} compare --baseline report.json --candidate worse.json >/dev/null 2>&1
status=$?
set -e
test "$status" -eq 1 ; check "compare catches a dropped metric" $?

"$PY" -m {{ package_name }} compare --baseline report.json --candidate worse.json \
  --tolerance 0.5 >/dev/null ; check "tolerance can allow a drop" $?

fewer=$("$PY" -m {{ package_name }} eval --size 20 --overlap 0 | grep '^chunks')
many=$("$PY" -m {{ package_name }} eval | grep '^chunks')
test "$fewer" != "$many" ; check "chunking settings change the index" $?

set +e
"$PY" -m {{ package_name }} eval --qrels missing.json >/dev/null 2>&1
status=$?
set -e
test "$status" -eq 2 ; check "a missing qrels file exits 2" $?

"$PY" -m {{ package_name }} selftest >/dev/null ; check "selftest passes" $?
"$PY" -m {{ package_name }} --version | grep -q '{{ npm_name }}' ; check "version prints" $?

rm -f report.json worse.json

if [ "$failures" -ne 0 ]; then
  printf 'smoke: %d check(s) failed\n' "$failures"
  exit 1
fi
printf 'smoke: all checks passed\n'
