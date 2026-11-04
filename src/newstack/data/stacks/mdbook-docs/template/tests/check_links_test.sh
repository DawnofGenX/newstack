#!/usr/bin/env bash
# Every case builds its own throwaway book: a failure names one rule instead of
# a pile of state left behind by the previous case.

make_book() { # dir
  local dir=$1
  mkdir -p "$dir/src/guide"
  cat >"$dir/src/SUMMARY.md" <<'MD'
# Summary

[Introduction](index.md)

- [Guide](guide/one.md)
MD
  cat >"$dir/src/index.md" <<'MD'
# Introduction

Read the [guide](guide/one.md).
MD
  cat >"$dir/src/guide/one.md" <<'MD'
# Guide

Back to the [start](../index.md).
MD
}

case_dir() { # name
  local dir="$TMP/$1"
  make_book "$dir"
  printf '%s' "$dir"
}

suite_checker() {
  local book

  book=$(case_dir good)
  run_capture "$CHECK" "$book"
  check "an intact book exits 0" 0 "$STATUS"
  # Two links in the pages, two in the summary.
  check "an intact book reports what it read" "checked 3 file(s), 4 link(s): ok" "$OUT"

  book=$(case_dir broken)
  printf '\nSee the [missing page](missing.md).\n' >>"$book/src/guide/one.md"
  run_capture "$CHECK" "$book"
  check "a broken link exits 1" 1 "$STATUS"
  check_contains "a broken link is reported with its line" "src/guide/one.md:5: missing.md does not exist" "$OUT"
  check_contains "the report counts the problem" "1 problem(s)" "$OUT"

  book=$(case_dir image)
  printf '\n![diagram](images/none.png)\n' >>"$book/src/guide/one.md"
  run_capture "$CHECK" "$book"
  check "a missing image exits 1" 1 "$STATUS"
  check_contains "a missing image is reported" "images/none.png does not exist" "$OUT"

  book=$(case_dir anchors)
  printf '\nSee [the top](../index.md#introduction) and [here](#guide).\n' >>"$book/src/guide/one.md"
  run_capture "$CHECK" "$book"
  check "anchors do not count as broken paths" 0 "$STATUS"

  book=$(case_dir external)
  printf '\n[site](https://example.com/x) [mail](mailto:a@example.com)\n' >>"$book/src/guide/one.md"
  run_capture "$CHECK" "$book"
  check "external links are left alone" 0 "$STATUS"

  book=$(case_dir orphan)
  printf '# Forgotten\n' >"$book/src/orphan.md"
  run_capture "$CHECK" "$book"
  check "an orphan page exits 1" 1 "$STATUS"
  check_contains "an orphan page is named" "src/orphan.md: not listed in src/SUMMARY.md" "$OUT"
  printf '\n- [Forgotten](orphan.md)\n' >>"$book/src/SUMMARY.md"
  run_capture "$CHECK" "$book"
  check "listing the page fixes it" 0 "$STATUS"

  book=$(case_dir nosummary)
  rm "$book/src/SUMMARY.md"
  run_capture "$CHECK" "$book"
  check "a missing summary exits 1" 1 "$STATUS"
  check_contains "a missing summary is named" "src/SUMMARY.md: missing" "$OUT"

  run_capture "$CHECK" --help
  check "--help exits 0" 0 "$STATUS"
  check_contains "--help prints the usage" "Usage: check-links.sh [ROOT]" "$OUT"
  run_capture "$CHECK" "$TMP" "$TMP"
  check "too many arguments exits 2" 2 "$STATUS"
  run_capture "$CHECK" "$TMP/nowhere"
  check "a missing directory exits 2" 2 "$STATUS"
  mkdir -p "$TMP/empty"
  run_capture "$CHECK" "$TMP/empty"
  check "a directory without src/ exits 2" 2 "$STATUS"
  check_contains "the missing src/ is explained" "has no src/ directory" "$ERR"
}

suite_book() {
  # The real book in this project must be clean, and it must build.
  run_capture "$CHECK"
  check "the shipped book passes the checker" 0 "$STATUS"

  if command -v mdbook >/dev/null 2>&1; then
    run_capture mdbook build "$ROOT"
    check "mdbook builds the book" 0 "$STATUS"
    check "the build writes index.html" 1 "$([ -f "$ROOT/book/index.html" ] && echo 1 || echo 0)"
    # A page from each section must be rendered, not just the index.
    check_contains "the guide page is rendered" "Write a page" \
      "$(cat "$ROOT/book/guide/writing.html" 2>/dev/null || echo "")"
    check_contains "the reference page is rendered" "make build" \
      "$(cat "$ROOT/book/reference/cli.html" 2>/dev/null || echo "")"
  else
    printf 'skip: mdbook is not installed, so the build is not exercised here\n' >&2
  fi
}
