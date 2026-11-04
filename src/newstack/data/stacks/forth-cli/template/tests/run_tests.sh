#!/bin/sh
# Two layers: the unit suite in Forth, then the real binary against the host wc.
set -u

root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root" || exit 1

prog=$root/bin/{{ npm_name }}
work=$root/tests/.tmp
rm -rf "$work"
mkdir -p "$work"

passed=0
failed=0

ok () { passed=$((passed + 1)); }
bad () { failed=$((failed + 1)); printf 'FAIL %s\n' "$1"; }

check_eq () { # name actual expected
  if [ "$2" = "$3" ]; then ok; else bad "$1 (got '$2', want '$3')"; fi
}

# 1. The unit suite, which prints the same tally shape we do.
unit=$(gforth tests/run_tests.fs 2>&1)
unit_status=$?
echo "$unit"
if [ "$unit_status" -ne 0 ]; then bad "unit suite exited $unit_status"; fi

unit_checks=$(printf '%s\n' "$unit" | sed -n 's/^checks: \([0-9]*\), passed: \([0-9]*\), failed: \([0-9]*\)$/\1/p')
unit_passed=$(printf '%s\n' "$unit" | sed -n 's/^checks: \([0-9]*\), passed: \([0-9]*\), failed: \([0-9]*\)$/\2/p')
unit_failed=$(printf '%s\n' "$unit" | sed -n 's/^checks: \([0-9]*\), passed: \([0-9]*\), failed: \([0-9]*\)$/\3/p')
if [ -z "$unit_checks" ]; then bad "unit suite printed no tally"; else
  passed=$((passed + unit_passed))
  failed=$((failed + unit_failed))
fi

# 2. Fixtures for the comparisons below.
printf 'alpha beta\ngamma delta\n' > "$work/p1.txt"
printf 'alpha beta\ngamma' > "$work/p2.txt"
printf 'h\303\251llo w\303\266rld\n' > "$work/p3.txt"
: > "$work/p4.txt"
printf 'a\tb\vc\fd\n' > "$work/p5.txt"

# 3. Whole rows, byte for byte, against the host wc.
for f in "$work"/p1.txt "$work"/p2.txt "$work"/p3.txt "$work"/p4.txt "$work"/p5.txt; do
  name=$(basename "$f")
  ours=$("$prog" -l -w -c "$f")
  theirs=$(wc -l -w -c "$f")
  check_eq "wc parity $name" "$ours" "$theirs"
done

# 4. A shared width and a total row for several operands.
ours=$("$prog" -l -w -c "$work/p1.txt" "$work/p2.txt")
theirs=$(wc -l -w -c "$work/p1.txt" "$work/p2.txt")
check_eq "wc parity two files" "$ours" "$theirs"

ours=$("$prog" -l -w -c "$work/p1.txt" "$work/p4.txt" "$work/p5.txt")
theirs=$(wc -l -w -c "$work/p1.txt" "$work/p4.txt" "$work/p5.txt")
check_eq "wc parity three files" "$ours" "$theirs"

# 5. One figure at a time keeps wc's own width.
for flags in "-l" "-w" "-c" "-lw" "--bytes" "-l -c"; do
  # shellcheck disable=SC2086
  ours=$("$prog" $flags "$work/p1.txt")
  # shellcheck disable=SC2086
  theirs=$(wc $flags "$work/p1.txt")
  check_eq "wc parity $flags" "$ours" "$theirs"
done

# 6. Standard input, both implicit and as an explicit operand.
out=$(printf 'alpha beta\ngamma\n' | "$prog" -w)
check_eq "stdin implicit no label" "$out" "3"

out=$(printf 'alpha beta\ngamma\n' | "$prog" -w -)
check_eq "stdin explicit operand" "$out" "3 -"

out=$(printf 'alpha beta\ngamma\n' | "$prog" -l -w -c)
theirs=$(printf 'alpha beta\ngamma\n' | wc -l -w -c)
check_eq "stdin padded like wc" "$out" "$theirs"

out=$(printf '' | "$prog" -l -w -c)
theirs=$(printf '' | wc -l -w -c)
check_eq "empty stdin" "$out" "$theirs"

# 7. An unreadable operand: a complaint, no row, the total still printed.
"$prog" -l -w -c "$work/p1.txt" "$work/missing.txt" > "$work/out.txt" 2> "$work/err.txt"
status=$?
check_eq "missing operand status" "$status" "1"
check_eq "missing operand message" "$(cat "$work/err.txt")" "error: cannot open '$work/missing.txt'"
check_eq "missing operand still totals" "$(cat "$work/out.txt")" "$(wc -l -w -c "$work/p1.txt" "$work/missing.txt" 2>/dev/null)"

# 8. The exit contract.
"$prog" --help > /dev/null 2>&1
check_eq "help status" "$?" "0"
out=$("$prog" --version)
check_eq "version output" "$out" "0.1.0"
"$prog" --version > /dev/null 2>&1
check_eq "version status" "$?" "0"

"$prog" --bogus > /dev/null 2> "$work/err.txt"
check_eq "usage error status" "$?" "2"
check_eq "usage error first line" "$(sed -n 1p "$work/err.txt")" "{{ npm_name }}: unknown option: --bogus"
check_eq "usage error second line" "$(sed -n 2p "$work/err.txt")" "Try '{{ npm_name }} --help' for more information."

# 9. The wrapper works from anywhere.
out=$(cd /tmp && "$prog" -l "$work/p1.txt")
theirs=$(wc -l "$work/p1.txt")
check_eq "wrapper outside the project" "$out" "$theirs"

rm -rf "$work"

checks=$((passed + failed))
printf 'checks: %s, passed: %s, failed: %s\n' "$checks" "$passed" "$failed"
[ "$failed" -eq 0 ] || exit 1
