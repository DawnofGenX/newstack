#!/usr/bin/env bash
# Smoke test for the generated project: the README's claims, checked from the
# outside, with the exit codes a caller would actually branch on.
set -uo pipefail

MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PY:-${ROOT}/.venv/bin/python}"

passed=0
failed=0

ok() {
    passed=$((passed + 1))
    printf 'ok   %s\n' "$1"
}

bad() {
    failed=$((failed + 1))
    printf 'FAIL %s\n' "$1"
    if [ -n "${2:-}" ]; then printf '       %s\n' "$2"; fi
}

check() {
    local name="$1"
    shift
    if "$@" >/dev/null 2>&1; then ok "$name"; else bad "$name" "exited non-zero"; fi
}

check_status() {
    local name="$1" want="$2" got="$3"
    if [ "$got" -eq "$want" ]; then
        ok "$name"
    else
        bad "$name" "exit $got, wanted $want"
    fi
}

check_equal() {
    local name="$1" want="$2" got="$3"
    if [ "$want" = "$got" ]; then ok "$name"; else bad "$name" "got '$got', wanted '$want'"; fi
}

check_contains() {
    local name="$1" needle="$2" file="$3"
    if grep -Fq -- "$needle" "$file"; then ok "$name"; else bad "$name" "missing '$needle'"; fi
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

SECRET="smoke-secret"
NOW=1780000000

"$PY" -m "$MODULE" demo >"$WORK/demo.txt" 2>&1
check_status "demo exits zero" 0 "$?"
check_equal "six stories hold" 6 "$(grep -Fc -- "-> holds" "$WORK/demo.txt")"
if grep -Fq -- "BROKEN" "$WORK/demo.txt"; then
    bad "no story is broken" "the demo printed BROKEN"
else
    ok "no story is broken"
fi
check_contains "the reordering story holds" \
    "reordering the query does not invalidate" "$WORK/demo.txt"
check_contains "the spelling story holds" "two spellings of one path agree" "$WORK/demo.txt"
check_contains "the replay story holds" "cannot be used twice" "$WORK/demo.txt"
check_contains "the naive signature differs" "and those differ" "$WORK/demo.txt"

"$PY" -m "$MODULE" sign --url "/a?b=2&a=1" --secret "$SECRET" --timestamp "$NOW" \
    >"$WORK/sign.txt" 2>&1
check_status "sign exits zero" 0 "$?"
check_contains "sign names the algorithm" "algorithm    hmac-sha256" "$WORK/sign.txt"
check_contains "sign canonicalises the query" "/a?a=1&b=2" "$WORK/sign.txt"
check_contains "sign reports the lifetime" "300 s of life" "$WORK/sign.txt"

"$PY" -m "$MODULE" sign --url "/a?b=2&a=1" --secret "$SECRET" --timestamp "$NOW" --json \
    >"$WORK/sign.json" 2>&1
check_status "sign --json exits zero" 0 "$?"
check "the json holds a 64 character signature" "$PY" -c \
    'import json,sys; d=json.load(open(sys.argv[1]));
assert d["algorithm"]=="hmac-sha256", d; assert len(d["signature"])==64, d' "$WORK/sign.json"

"$PY" -m "$MODULE" sign --url "/a?b=2&a=1" --secret "$SECRET" --timestamp "$NOW" --json \
    >"$WORK/sign_reordered.json" 2>&1
"$PY" -m "$MODULE" sign --url "/a?a=1&b=2" --secret "$SECRET" --timestamp "$NOW" --json \
    >"$WORK/sign_plain.json" 2>&1
check "a reordering produces the same signature" "$PY" -c \
    'import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]));
assert a["signature"]==b["signature"], (a,b)' "$WORK/sign_reordered.json" "$WORK/sign_plain.json"

"$PY" -m "$MODULE" sign --url "/a" --secret "$SECRET" --timestamp "$NOW" --show-string \
    >"$WORK/string.txt" 2>&1
check_status "--show-string exits zero" 0 "$?"
check_contains "--show-string prints the covered text" "signing string" "$WORK/string.txt"
check_contains "--show-string shows the method line" "GET" "$WORK/string.txt"

"$PY" -m "$MODULE" verify --url "/a?a=1&b=2" --secret "$SECRET" --now "$NOW" \
    --signature-file "$WORK/sign_reordered.json" >"$WORK/verify.txt" 2>&1
check_status "a copied request verifies" 0 "$?"
check_contains "an accepted signature says ok" "ok       accepted" "$WORK/verify.txt"

"$PY" -m "$MODULE" verify --url "/b" --secret "$SECRET" --now "$NOW" \
    --signature-file "$WORK/sign.json" >"$WORK/tampered.txt" 2>&1
check_status "a different path exits one" 1 "$?"
check_contains "a different path is named" "does not match this request" "$WORK/tampered.txt"

"$PY" -m "$MODULE" sign --url "/a" --secret "$SECRET" --timestamp "$NOW" --json \
    >"$WORK/fresh.json" 2>&1
"$PY" -m "$MODULE" verify --url "/a" --secret "$SECRET" --now "$((NOW + 301))" \
    --signature-file "$WORK/fresh.json" >"$WORK/expired.txt" 2>&1
check_status "an expired signature exits one" 1 "$?"
check_contains "an expired signature names the delay" "expired 1 s ago" "$WORK/expired.txt"

"$PY" -m "$MODULE" verify --url "/a" --secret "another-secret" --now "$NOW" \
    --signature-file "$WORK/fresh.json" >"$WORK/wrongsecret.txt" 2>&1
check_status "a wrong secret exits one" 1 "$?"
check_contains "a wrong secret is a mismatch" "does not match" "$WORK/wrongsecret.txt"

"$PY" -m "$MODULE" sign --url "https://example.test/a" --secret "$SECRET" \
    --timestamp "$NOW" >"$WORK/host.txt" 2>&1
check_status "a host is refused with exit two" 2 "$?"
check_contains "the host refusal explains itself" "sign the path" "$WORK/host.txt"

"$PY" -m "$MODULE" verify --url "/a" --secret "$SECRET" --now "$NOW" \
    >"$WORK/nosig.txt" 2>&1
check_status "verify without a signature exits two" 2 "$?"
check_contains "verify names the missing flag" "--signature" "$WORK/nosig.txt"

"$PY" -m "$MODULE" sign --url "/a" --secret "$SECRET" --ttl 0 --timestamp "$NOW" \
    >"$WORK/ttl.txt" 2>&1
check_status "a zero ttl exits two" 2 "$?"
check_contains "a zero ttl explains itself" "positive" "$WORK/ttl.txt"

"$PY" -m "$MODULE" string --url "/a" --timestamp "$NOW" >"$WORK/plain.txt" 2>&1
check_status "string exits zero" 0 "$?"
check_equal "the signing string has five lines" 5 \
    "$(grep -c . "$WORK/plain.txt")"

"$PY" -m "$MODULE" --version >"$WORK/version.txt" 2>&1
check_status "the version banner exits zero" 0 "$?"
check_contains "the banner names the program" "$PROGRAM 0.1.0" "$WORK/version.txt"

"$PY" -m "$MODULE" --help >"$WORK/help.txt" 2>&1
check_status "help exits zero" 0 "$?"
check_contains "help lists sign" "sign" "$WORK/help.txt"
check_contains "help lists verify" "verify" "$WORK/help.txt"

"$PY" -m "$MODULE" selftest >"$WORK/selftest.txt" 2>&1
check_status "selftest exits zero" 0 "$?"
check_contains "selftest reports its checks" "checks passed" "$WORK/selftest.txt"

printf '\nsmoke: %d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then exit 1; fi
