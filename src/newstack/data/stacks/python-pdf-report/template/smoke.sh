#!/usr/bin/env bash
# smoke.sh — the CLI end to end: build a report, read it back, build it again and
# compare the bytes. No port, no server; the deliverable is a file.
set -euo pipefail

PY="${PY:-.venv/bin/python}"

# Run from the project root so fixtures/ resolves regardless of the caller.
work="$(mktemp -d)"
failures=0
cleanup() { rm -rf "$work"; }
trap cleanup EXIT

check() { # check <label> <expected> <actual>
  if [ "$2" = "$3" ]; then
    printf 'ok   %s\n' "$1"
  else
    printf 'FAIL %s\n  expected: %s\n  actual:   %s\n' "$1" "$2" "$3"
    failures=$((failures + 1))
  fi
}

contains() { # contains <label> <needle> <haystack>
  case "$3" in
    *"$2"*) printf 'ok   %s\n' "$1" ;;
    *) printf 'FAIL %s\n  wanted substring: %s\n  in: %s\n' "$1" "$2" "$3"
       failures=$((failures + 1)) ;;
  esac
}

summary="$("$PY" -m {{ package_name }}.cli --input fixtures/records.ndjson --output "$work/a.pdf" \
  --title "Smoke" --json)"
contains "the summary reports three records" '"records": 3' "$summary"
contains "the summary counts utf8 bytes" '"bytes": 33' "$summary"
check "the summary reports one page" '"pages": 1' "$(printf '%s' "$summary" | grep -o '"pages": 1')"

head -c 5 "$work/a.pdf" >"$work/magic"
check "the output starts with %PDF-" '%PDF-' "$(cat "$work/magic")"

# Reading the PDF back is the only check that proves the numbers are IN the file:
# a broken layout can hold the right summary in the process and drop it on the page.
text="$("$PY" - "$work/a.pdf" <<'PY'
import sys
from pypdf import PdfReader
print("\n".join(page.extract_text() or "" for page in PdfReader(sys.argv[1]).pages))
PY
)"
contains "the table carries the alpha row" 'alpha' "$text"
contains "the table carries the beta row" 'beta' "$text"
contains "the totals line is on the page" 'totals: 3 lines, 8 words, 33 bytes' "$text"
contains "utf8 bytes survive as a number, not as mojibake" '14' "$text"

"$PY" -m {{ package_name }}.cli --input fixtures/records.ndjson --output "$work/b.pdf" --title "Smoke" >/dev/null
if cmp -s "$work/a.pdf" "$work/b.pdf"; then
  printf 'ok   the same input produced identical bytes\n'
else
  printf 'FAIL the same input produced different bytes — the report is not reproducible\n'
  failures=$((failures + 1))
fi

set +e
"$PY" -m {{ package_name }}.cli --input fixtures/broken.ndjson --output "$work/c.pdf" >"$work/bad.out" 2>&1
status=$?
set -e
check "bad input exits 2" '2' "$status"
contains "bad input names the line" 'line 2: not JSON' "$(cat "$work/bad.out")"
if [ -e "$work/c.pdf" ]; then
  printf 'FAIL a refused input still wrote a PDF\n'
  failures=$((failures + 1))
else
  printf 'ok   a refused input left no PDF behind\n'
fi

if [ "$failures" -ne 0 ]; then
  printf 'smoke: %d check(s) failed\n' "$failures" >&2
  exit 1
fi
printf 'smoke: all checks passed\n'
