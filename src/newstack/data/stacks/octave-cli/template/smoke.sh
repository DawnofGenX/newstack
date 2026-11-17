#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v octave >/dev/null 2>&1; then
  case "octave" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: octave is missing (install octave)"; exit 1 ;;
  esac
fi

echo "smoke: octave-cli"

if (
octave --no-window-system --quiet tests/run_tests.m
); then ok "test"; else bad "test"; fi

if (
./bin/{{ npm_name }} --help | grep -q 'Usage: {{ npm_name }}'
); then ok "help"; else bad "help"; fi

if (
set +e; ./bin/{{ npm_name }} --bogus >/dev/null 2>&1; status=$?; test "$status" -eq 2
); then ok "usage-error"; else bad "usage-error"; fi

if (
set +e; ./bin/{{ npm_name }} /nonexistent/file.txt >/dev/null 2>&1; status=$?; test "$status" -eq 1
); then ok "missing-file"; else bad "missing-file"; fi

if (
test "$(printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w)" = '3 -' && test "$(printf 'alpha beta\ngamma delta\n' | ./bin/{{ npm_name }})" = ' 2  4 23 -'
); then ok "stdin"; else bad "stdin"; fi

if (
test "$(printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w -)" = '3 -'
); then ok "dash-operand"; else bad "dash-operand"; fi

if (
mkdir -p .parity && printf 'alpha beta\\ngamma delta\\n' > .parity/p1.txt && printf 'one two three' > .parity/p2.txt && printf 'h\\303\\251llo w\\303\\266rld\\n' > .parity/p3.txt && : > .parity/p4.txt && printf 'a\\tb\\vc\\fd\\n' > .parity/p5.txt && ok=0; for file in .parity/p*.txt; do ours=$(./bin/{{ npm_name }} -l -w -c "$file" | awk '{print $1, $2, $3}'); theirs=$(wc -l -w -c < "$file" | awk '{print $1, $2, $3}'); if [ "$ours" != "$theirs" ]; then echo "mismatch on $file: ours=$ours wc=$theirs"; ok=1; fi; done; test "$ok" -eq 0
); then ok "parity"; else bad "parity"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
