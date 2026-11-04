#!/usr/bin/env bash
# Our counts must be wc's counts, byte for byte, padding included.
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$root/.parity"
rm -rf "$work"
mkdir -p "$work"

printf 'alpha beta\ngamma delta\n' > "$work/plain.txt"
printf 'one two three' > "$work/no-trailing-newline.txt"
printf 'h\xc3\xa9llo w\xc3\xb6rld\n' > "$work/utf8.txt"
: > "$work/empty.txt"
printf 'a\tb\vc\fd\n' > "$work/controls.txt"
printf 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa b\n' > "$work/wide.txt"

pass=0
fail=0
compare() {
  local label="$1" args="$2"
  "$root/build/app" $args > "$work/ours.out" 2> "$work/ours.err"
  local ours_status=$?
  wc $args > "$work/wc.out" 2> "$work/wc.err"
  local wc_status=$?
  if cmp -s "$work/ours.out" "$work/wc.out" && [ "$ours_status" = "$wc_status" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL $label"
    diff <(cat -A "$work/ours.out") <(cat -A "$work/wc.out") | head -4
    echo "  status: ours=$ours_status wc=$wc_status"
  fi
}

for file in plain.txt no-trailing-newline.txt utf8.txt empty.txt controls.txt wide.txt; do
  for flags in "" "-l" "-w" "-c" "-lw" "-lc" "-wc" "-lwc"; do
    compare "$flags $file" "$flags $work/$file"
  done
done

compare "two files" "$work/plain.txt $work/utf8.txt"
compare "five files" "$work/plain.txt $work/utf8.txt $work/empty.txt $work/controls.txt $work/wide.txt"
compare "five files -w" "-w $work/plain.txt $work/utf8.txt $work/empty.txt $work/controls.txt $work/wide.txt"
compare "clustered flags" "-lwc $work/plain.txt $work/utf8.txt"
compare "long flags" "--lines --bytes $work/plain.txt $work/utf8.txt"
compare "missing file" "$work/plain.txt $work/gone.txt"

stdin_compare() {
  local label="$1" flags="$2" payload="$3"
  printf '%s' "$payload" | "$root/build/app" $flags > "$work/ours.out" 2>/dev/null
  local ours_status=$?
  printf '%s' "$payload" | wc $flags > "$work/wc.out" 2>/dev/null
  if cmp -s "$work/ours.out" "$work/wc.out" && [ "$ours_status" = 0 ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL $label"
    diff <(cat -A "$work/ours.out") <(cat -A "$work/wc.out") | head -4
  fi
}

stdin_compare "stdin" "" $'alpha beta\ngamma\n'
stdin_compare "stdin -w" "-w" $'alpha beta\ngamma\n'
stdin_compare "stdin -l" "-l" $'alpha beta\ngamma\n'
stdin_compare "stdin -c" "-c" $'alpha beta\ngamma\n'
stdin_compare "stdin -lwc" "-lwc" $'alpha beta\ngamma\n'

rm -rf "$work"
echo "parity: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
