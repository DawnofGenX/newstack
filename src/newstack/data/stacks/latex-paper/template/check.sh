#!/usr/bin/env bash
# Rebuild the paper, then assert what a reader would actually see.
set -euo pipefail

cd "$(dirname "$0")"
PDF=build/paper.pdf
TEXT=$(mktemp)
trap 'rm -f "$TEXT"' EXIT

make -s build > /dev/null

if [ ! -s "$PDF" ]; then
  echo "FAIL no pdf at $PDF" >&2
  exit 1
fi
head -c 5 "$PDF" | grep -q '%PDF-' || { echo "FAIL $PDF is not a pdf" >&2; exit 1; }

pdftotext "$PDF" "$TEXT"

check() {
  if ! grep -Fq -- "$2" "$TEXT"; then
    echo "FAIL the pdf does not contain: $2" >&2
    exit 1
  fi
  echo "ok  $1"
}

check title {{ title }}
check section Introduction
check method Method
check results Results
check citation '[1]'
check reference 'Literate Programming'

pages=$(pdfinfo "$PDF" | awk '/^Pages:/ {print $2}')
if [ "$pages" != "2" ]; then
  echo "FAIL expected 2 pages, got $pages" >&2
  exit 1
fi
echo "ok  two pages"

if grep -q 'Overfull \\hbox' build/paper.log; then
  echo "FAIL the build has overfull lines" >&2
  grep 'Overfull \\hbox' build/paper.log >&2
  exit 1
fi
echo "ok  no overfull boxes"

if grep -qE 'LaTeX Warning: (Citation|Reference)' build/paper.log; then
  echo "FAIL undefined citations or references" >&2
  grep -E 'LaTeX Warning: (Citation|Reference)' build/paper.log >&2
  exit 1
fi
echo "ok  every citation resolved"

if grep -Fq '??' "$TEXT"; then
  echo "FAIL the text still shows a ?? placeholder" >&2
  exit 1
fi
echo "ok  no unresolved references"

echo "check: all checks passed"
