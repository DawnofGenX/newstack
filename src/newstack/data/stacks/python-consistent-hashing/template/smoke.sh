#!/usr/bin/env bash
# Real runs of the CLI: the happy paths, and every gate failing on purpose.
set -uo pipefail

PY=${PY:-python3}
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
passed=0
failed=0

ok() { printf 'ok   %s\n' "$1"; passed=$((passed + 1)); }
bad() { printf 'FAIL %s\n' "$1"; failed=$((failed + 1)); }
check() { if [ "$2" -eq 0 ]; then ok "$1"; else bad "$1"; fi; }

OUT=""

run() {
    OUT=$("$PY" -m "$MODULE" "$@" 2>&1)
    return $?
}

# ---- version and help -------------------------------------------------------
run --version
check "--version names the program" $([ $? -eq 0 ] && echo "$OUT" | grep -q "$PROGRAM " && echo 0 || echo 1)

run --help
check "--help exits 0" $([ $? -eq 0 ] && echo 0 || echo 1)

run nope
check "an unknown command exits 2" $([ $? -eq 2 ] && echo 0 || echo 1)

# ---- map --------------------------------------------------------------------
run map --nodes alpha,bravo,charlie --keys 3000
status=$?
check "map exits 0" $([ "$status" -eq 0 ] && echo 0 || echo 1)
check "map prints an imbalance" $(echo "$OUT" | grep -q "^imbalance" && echo 0 || echo 1)
check "map prints one line per node" $([ "$(echo "$OUT" | grep -c '^charlie\|^alpha\|^bravo')" -ge 3 ] && echo 0 || echo 1)

run map --nodes alpha,bravo --keys 100 --json
check "map --json emits loads" $(echo "$OUT" | grep -q '\"loads\"' && echo 0 || echo 1)

run map --nodes alpha,alpha --keys 10
check "map refuses duplicate nodes" $([ $? -eq 2 ] && echo 0 || echo 1)

run map --nodes alpha --keys 0
check "map refuses zero keys" $([ $? -eq 2 ] && echo 0 || echo 1)

run map --nodes alpha --vnodes 0 --keys 10
check "map refuses zero vnodes" $([ $? -eq 2 ] && echo 0 || echo 1)

# ---- ring -------------------------------------------------------------------
run ring --nodes alpha,bravo,charlie --key user:00001
check "ring exits 0" $([ $? -eq 0 ] && echo 0 || echo 1)
check "ring names an owner" $(echo "$OUT" | grep -q "^owner" && echo 0 || echo 1)

run ring --nodes alpha --key user:00001 --weights bravo=2
check "ring accepts weights" $([ $? -eq 0 ] && echo 0 || echo 1)

run ring --nodes alpha --key user:00001 --weights bravo=x
check "ring refuses a malformed weight" $([ $? -eq 2 ] && echo 0 || echo 1)

run ring --nodes alpha
check "ring requires a key" $([ $? -eq 2 ] && echo 0 || echo 1)

# ---- move -------------------------------------------------------------------
run move --nodes alpha,bravo,charlie,delta,echo --add foxtrot --keys 5000
status=$?
check "move exits 0 inside the limit" $([ "$status" -eq 0 ] && echo 0 || echo 1)
moved=$(echo "$OUT" | awk '/^moved/ {print $2}')
check "move reports a share, not everything" $([ "${moved:-9999}" -lt 1250 ] && echo 0 || echo 1)
modulo=$(echo "$OUT" | awk '/^modulo/ {print $1}')
check "move compares with modulo" $(echo "$OUT" | grep -q "^modulo *[0-9]" && echo 0 || echo 1)
check "move reports zero strangers" $(echo "$OUT" | grep -q "^strangers    0 " && echo 0 || echo 1)

run move --nodes alpha,bravo,charlie --add delta --keys 3000 --max-moved 1
status=$?
check "move gates on the movement" $([ "$status" -eq 1 ] && echo 0 || echo 1)
check "move says why it failed" $(echo "$OUT" | grep -q "gate         FAIL" && echo 0 || echo 1)

run move --nodes alpha,bravo --add bravo --keys 100
check "move refuses an existing node" $([ $? -eq 2 ] && echo 0 || echo 1)

run move --nodes alpha --add bravo --keys 100 --show 2
check "move can show the moves" $(echo "$OUT" | grep -q -- "->" && echo 0 || echo 1)

# ---- balance ----------------------------------------------------------------
run balance --nodes alpha,bravo,charlie --keys 5000
check "balance passes an even split" $([ $? -eq 0 ] && echo 0 || echo 1)

run balance --nodes alpha,bravo,charlie --keys 5000 --max-imbalance 1.0
check "balance gates an uneven split" $([ $? -eq 1 ] && echo 0 || echo 1)

run balance --nodes solo --keys 100
status=$?
check "a single node is a perfect split" $([ "$status" -eq 0 ] && echo "$OUT" | grep -q "1.00" && echo 0 || echo 1)

# ---- demo and selftest ------------------------------------------------------
run demo
check "demo exits 0" $([ $? -eq 0 ] && echo 0 || echo 1)
check "demo has all six stories" $([ "$(echo "$OUT" | grep -c '^[1-6]\. ')" -eq 6 ] && echo 0 || echo 1)
check "demo shows the vnode table" $(echo "$OUT" | grep -q "arc imbalance" && echo 0 || echo 1)
check "demo shows wraparound" $(echo "$OUT" | grep -q "the ring wraps" && echo 0 || echo 1)

run selftest
check "selftest passes" $([ $? -eq 0 ] && echo 0 || echo 1)
check "selftest reports its checks" $(echo "$OUT" | grep -q "checks passed" && echo 0 || echo 1)

printf 'smoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
