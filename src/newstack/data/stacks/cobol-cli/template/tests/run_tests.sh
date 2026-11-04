#!/usr/bin/env bash
# Runs the unit driver, then checks the built tool against the real wc on this
# machine. Prints one PASS/FAIL line per assertion and a tally at the end.
set -u

here=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
root=$(CDPATH='' cd -- "$here/.." && pwd)
cd "$root"

tmp=$here/.tmp
rm -rf "$tmp"
mkdir -p "$tmp"
trap 'rm -rf "$tmp"' EXIT INT TERM

checks=0
passed=0
failed=0

pass() {
  checks=$((checks + 1)); passed=$((passed + 1))
  printf 'PASS %s\n' "$1"
}

fail() {
  checks=$((checks + 1)); failed=$((failed + 1))
  printf 'FAIL %s (%s)\n' "$1" "$2"
}

# check_name DESCRIPTION EXPECTED ACTUAL
check_name() {
  if [ "$2" = "$3" ]; then pass "$1"; else fail "$1" "want [$2], got [$3]"; fi
}

# same_as_wc NAME ARGS... -- compares our output and our exit code with wc's
same_as_wc() {
  local name=$1; shift
  local ours theirs ours_rc theirs_rc
  ours=$("$bin" "$@" 2>/dev/null); ours_rc=$?
  theirs=$(wc "$@" 2>/dev/null); theirs_rc=$?
  if [ "$ours" = "$theirs" ] && [ "$ours_rc" = "$theirs_rc" ]; then
    pass "$name"
  else
    fail "$name" "ours [${ours}] rc=${ours_rc}, wc [${theirs}] rc=${theirs_rc}"
  fi
}

bin=${1:-}
if [ -z "$bin" ]; then
  for candidate in build/*; do
    if [ -x "$candidate" ] && [ "${candidate##*/}" != "textstat-tests" ]; then
      bin=$candidate
      break
    fi
  done
fi
if [ -z "$bin" ] || [ ! -x "$bin" ]; then
  echo "run_tests: no built binary; run 'make all' first" >&2
  exit 1
fi

unit=build/textstat-tests
if [ ! -x "$unit" ]; then
  echo "run_tests: build/textstat-tests is missing; run 'make all' first" >&2
  exit 1
fi

# The unit driver counts its own assertions; fold its tally into ours.
unit_out=$("$unit")
unit_rc=$?
if [ "$unit_rc" -ne 0 ]; then
  printf '%s\n' "$unit_out" | grep '^FAIL ' || true
fi
unit_tally=$(printf '%s\n' "$unit_out" | sed -n 's/^checks: \([0-9]*\), passed: \([0-9]*\), failed: \([0-9]*\)$/\1 \2 \3/p')
if [ -z "$unit_tally" ]; then
  fail "the unit driver printed a tally" "rc=${unit_rc}, no tally line"
else
  set -- $unit_tally
  checks=$((checks + $1)); passed=$((passed + $2)); failed=$((failed + $3))
  if [ "$3" -eq 0 ]; then
    pass "the unit driver is green"
  else
    fail "the unit driver is green" "$3 failing assertion(s)"
  fi
fi

# fixtures, written the way printf writes them: no shell echo surprises
printf 'alpha beta\ngamma delta\n' > "$tmp/plain.txt"
printf 'one line, no trailing newline' > "$tmp/tail.txt"
printf 'h\xc3\xa9llo w\xc3\xb6rld\n' > "$tmp/utf8.txt"
: > "$tmp/empty.txt"
printf 'alpha\vbeta\fgamma\rdelta\n' > "$tmp/control.txt"
python3 -c 'import sys; open(sys.argv[1], "w").write("x" * 1200 + "\n")' "$tmp/wide.txt" 2>/dev/null ||
  perl -e 'print "x" x 1200, "\n"' > "$tmp/wide.txt"

for name in plain tail utf8 empty control wide; do
  same_as_wc "matches wc on ${name}.txt" -l -w -c "$tmp/${name}.txt"
done

same_as_wc "matches wc for lines only" -l "$tmp/plain.txt"
same_as_wc "matches wc for bytes only" -c "$tmp/plain.txt"
same_as_wc "matches wc for words only" -w "$tmp/plain.txt"
same_as_wc "matches wc for a cluster" -lw "$tmp/plain.txt"
same_as_wc "matches wc for long flags" --lines --bytes "$tmp/plain.txt"
same_as_wc "matches wc for two files" -l -w -c "$tmp/plain.txt" "$tmp/utf8.txt"
same_as_wc "matches wc for a wide file" -l -w "$tmp/wide.txt"

check_name "a lone figure keeps its natural width" \
  "$(wc -l "$tmp/plain.txt")" "$("$bin" -l "$tmp/plain.txt")"

check_name "an empty file counts zero" \
  "0 0 0 $tmp/empty.txt" "$("$bin" "$tmp/empty.txt")"

out=$(printf 'alpha beta\ngamma\n' | "$bin" -w)
check_name "reads a pipe without an operand" "$(printf 'alpha beta\ngamma\n' | wc -w)" "$out"

out=$(printf 'alpha beta\ngamma\n' | "$bin" -w -)
check_name "reads a dash operand" "$(printf 'alpha beta\ngamma\n' | wc -w -)" "$out"

out=$(printf 'alpha beta\ngamma\n' | "$bin")
check_name "a pipe with no flag shows every figure" \
  "$(printf 'alpha beta\ngamma\n' | wc -l -w -c)" "$out"

out=$("$bin" --help); rc=$?
check_name "help exits zero" "0" "$rc"
case $out in
  *"Usage:"*) pass "help prints a usage line" ;;
  *) fail "help prints a usage line" "no Usage: in [$out]" ;;
esac

out=$("$bin" --version); rc=$?
check_name "version exits zero" "0" "$rc"
check_name "version prints the version" "0.1.0" "$out"

"$bin" --bogus > "$tmp/out.txt" 2> "$tmp/err.txt"; rc=$?
check_name "an unknown option exits two" "2" "$rc"
case $(sed -n 1p "$tmp/err.txt") in
  *": unknown option: --bogus") pass "an unknown option names itself" ;;
  *) fail "an unknown option names itself" "got [$(sed -n 1p "$tmp/err.txt")]" ;;
esac
check_name "an unknown option points at help" "1" \
  "$(sed -n 2p "$tmp/err.txt" | grep -c -- "--help' for more information")"

"$bin" "$tmp/missing.txt" > "$tmp/out.txt" 2> "$tmp/err.txt"; rc=$?
check_name "a missing file exits one" "1" "$rc"
check_name "a missing file says so" "1" \
  "$(grep -c "error: cannot open" "$tmp/err.txt")"

out=$("$bin" "$tmp/plain.txt" "$tmp/missing.txt" 2>/dev/null); rc=$?
check_name "a partly unreadable set exits one" "1" "$rc"
check_name "a partly unreadable set still totals" \
  "$(wc -l -w -c "$tmp/plain.txt" "$tmp/missing.txt" 2>/dev/null)" "$out"

out=$("$bin" "$tmp/plain.txt" "$tmp/missing.txt" 2>/dev/null | tail -1)
check_name "the total row survives a failure" \
  "$(wc -l -w -c "$tmp/plain.txt" "$tmp/missing.txt" 2>/dev/null | tail -1)" "$out"

"$bin" "$tmp" > "$tmp/out.txt" 2> "$tmp/err.txt"; rc=$?
check_name "a directory is refused" "1" "$rc"
check_name "a directory is named in the complaint" "1" \
  "$(grep -c "error: cannot open" "$tmp/err.txt")"

printf 'checks: %d, passed: %d, failed: %d\n' "$checks" "$passed" "$failed"
[ "$failed" -eq 0 ]
