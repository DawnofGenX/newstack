#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v erl >/dev/null 2>&1; then
  case "erl" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: erl is missing (install erl)"; exit 1 ;;
  esac
fi
if ! command -v erlc >/dev/null 2>&1; then
  case "erlc" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: erlc is missing (install erlc)"; exit 1 ;;
  esac
fi
if ! command -v make >/dev/null 2>&1; then
  case "make" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: make is missing (install make)"; exit 1 ;;
  esac
fi

echo "smoke: erlang-cli"

if (
make -s
); then ok "compile"; else bad "compile"; fi

if (
make -s test
); then ok "test"; else bad "test"; fi

if (
./bin/{{ npm_name }} --help
); then ok "help"; else bad "help"; fi

if (
./bin/{{ npm_name }} --bogus >/dev/null 2>&1; test $? -eq 2
); then ok "usage-error"; else bad "usage-error"; fi

if (
./bin/{{ npm_name }} does-not-exist.txt >/dev/null 2>&1; test $? -eq 1
); then ok "missing-file"; else bad "missing-file"; fi

if (
test "$(printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w)" = '3 -'
); then ok "stdin"; else bad "stdin"; fi

if (
printf 'alpha beta\ngamma delta\n' > .p1.txt && printf 'no trailing newline' > .p2.txt && printf 'h\303\251llo w\303\266rld\n' > .p3.txt && : > .p4.txt && printf 'a\tb\nc\vd\re\n' > .p5.txt && for f in .p1.txt .p2.txt .p3.txt .p4.txt .p5.txt; do ours=$(./bin/{{ npm_name }} -l -w -c "$f" | awk '{print $1, $2, $3}'); theirs=$(wc -l -w -c "$f" | awk '{print $1, $2, $3}'); if [ "$ours" != "$theirs" ]; then echo "MISMATCH $f: ours=[$ours] theirs=[$theirs]"; exit 1; fi; done && rm -f .p1.txt .p2.txt .p3.txt .p4.txt .p5.txt && echo "parity ok"
); then ok "parity"; else bad "parity"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
