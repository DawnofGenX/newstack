#!/usr/bin/env bash
# End-to-end checks against the installed command, not the modules.
#
#   PY=.venv/bin/python bash smoke.sh
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
ROUTES="fixtures/routes.txt"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAILS=0

ok() {
    PASS=$((PASS + 1))
    printf 'ok   %s\n' "$1"
}

bad() {
    FAILS=$((FAILS + 1))
    printf 'FAIL %s\n' "$1"
}

check_equal() {
    if [ "$2" = "$3" ]; then
        ok "$1"
    else
        bad "$1 (expected '$2', got '$3')"
    fi
}

check_contains() {
    case "$3" in
        *"$2"*) ok "$1" ;;
        *) bad "$1 (missing '$2' in: ${3:0:200})" ;;
    esac
}

run() {
    OUT="$("$@" 2>&1)"
    STATUS=$?
}

# --- the command answers at all ---------------------------------------------
run "$PY" -m "$MODULE" --version
check_equal "version exits zero" 0 "$STATUS"
check_contains "version names the program" "$PROGRAM" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists match" "match" "$OUT"
check_contains "help lists why" "why" "$OUT"

# --- the table ---------------------------------------------------------------
run "$PY" -m "$MODULE" table --routes "$ROUTES"
check_equal "table exits zero" 0 "$STATUS"
check_contains "the table counts its routes" "10 route(s)" "$OUT"
check_contains "a literal route is listed" "/users/me" "$OUT"
check_contains "a catch-all is listed" "/files/*rest" "$OUT"
check_contains "and its shape is spelled out" "static catchall" "$OUT"

# --- matching ----------------------------------------------------------------
run "$PY" -m "$MODULE" match --routes "$ROUTES" --path /users/me
check_equal "a literal match exits zero" 0 "$STATUS"
check_contains "and is reported as matched" "verdict    matched" "$OUT"
check_contains "the route is named" "route      GET /users/me" "$OUT"

run "$PY" -m "$MODULE" match --routes "$ROUTES" --path /users/42
check_contains "a parameter takes the segment" "route      GET /users/{id}" "$OUT"
check_contains "and binds it" "param      id = '42'" "$OUT"

run "$PY" -m "$MODULE" match --routes "$ROUTES" --path /users/42/posts
check_contains "a deeper route wins by depth" "route      GET /users/{id}/posts" "$OUT"

run "$PY" -m "$MODULE" match --routes "$ROUTES" --path /files/2026/11/a.txt
check_contains "a catch-all takes the rest" "route      GET /files/*rest" "$OUT"
check_contains "and keeps its slashes" "param      rest = '2026/11/a.txt'" "$OUT"

run "$PY" -m "$MODULE" match --routes "$ROUTES" --path /
check_equal "the root matches" 0 "$STATUS"
check_contains "the root route is served" "route      GET /" "$OUT"

# --- what a miss says --------------------------------------------------------
run "$PY" -m "$MODULE" match --routes "$ROUTES" --path /users/42/comments
check_equal "a miss exits one" 1 "$STATUS"
check_contains "and says there is no route" "verdict    no route" "$OUT"
check_contains "the reason names the segment" "segment 3 of the path is 'comments'" "$OUT"
check_contains "and a nearby route is offered" "hint" "$OUT"

# --- a wrong method is not a missing resource --------------------------------
run "$PY" -m "$MODULE" match --routes "$ROUTES" --method PATCH --path /users/42
check_equal "a wrong method exits one" 1 "$STATUS"
check_contains "and says so" "verdict    wrong method" "$OUT"
check_contains "the allow list is printed" "allow      DELETE, GET, PUT" "$OUT"

run "$PY" -m "$MODULE" why --routes "$ROUTES" --method PATCH --path /users/42
check_contains "why names the kind" "verdict    not-allowed" "$OUT"
check_contains "and reports which method answered" "GET     match  GET /users/{id}" "$OUT"

run "$PY" -m "$MODULE" why --routes "$ROUTES" --path /users/me
check_equal "why on a served path exits one" 1 "$STATUS"
check_contains "and says which route serves it" "is served by GET /users/me" "$OUT"

# --- refusals ----------------------------------------------------------------
run "$PY" -m "$MODULE" match --routes "$ROUTES" --path /users/42/
check_equal "a trailing slash is unusable" 2 "$STATUS"
check_contains "and says why" "trailing slash" "$OUT"

run "$PY" -m "$MODULE" match --routes "$ROUTES" --path '//users'
check_equal "an empty segment is unusable" 2 "$STATUS"
check_contains "and says so" "empty segment" "$OUT"

run "$PY" -m "$MODULE" match --routes "$ROUTES" --method TRACE --path /
check_equal "an unknown method is unusable" 2 "$STATUS"
check_contains "and lists the ones it knows" "not a method this router knows" "$OUT"

run "$PY" -m "$MODULE" match --routes /nope/routes.txt --path /
check_equal "a missing table is unusable" 2 "$STATUS"
check_contains "and is named" "no such route table" "$OUT"

printf '# nothing here\n' > "$WORK/empty.txt"
run "$PY" -m "$MODULE" match --routes "$WORK/empty.txt" --path /
check_equal "an empty table is unusable" 2 "$STATUS"
check_contains "and says a router needs routes" "holds no routes" "$OUT"

printf 'GET /a extra\n' > "$WORK/short.txt"
run "$PY" -m "$MODULE" table --routes "$WORK/short.txt"
check_equal "a malformed line is unusable" 2 "$STATUS"
check_contains "the line number is given" "short.txt:1" "$OUT"

printf 'GET /a\nPOST /a\nGET /a\n' > "$WORK/dup.txt"
run "$PY" -m "$MODULE" table --routes "$WORK/dup.txt"
check_equal "a duplicate route is unusable" 2 "$STATUS"
check_contains "and names the clash" "already registered" "$OUT"

printf 'GET /a/*rest/b\n' > "$WORK/mid.txt"
run "$PY" -m "$MODULE" table --routes "$WORK/mid.txt"
check_equal "a catch-all in the middle is unusable" 2 "$STATUS"
check_contains "and says nothing can follow it" "nothing can follow it" "$OUT"

# --- the payload -------------------------------------------------------------
run "$PY" -m "$MODULE" match --routes "$ROUTES" --path /files/a/b.txt --json
check_equal "json match exits zero" 0 "$STATUS"
run "$PY" -c "import json,sys; d=json.loads(sys.argv[1]); print(d['kind'], d['params']['rest'])" "$OUT"
check_equal "the payload carries the binding" "match a/b.txt" "$OUT"

run "$PY" -m "$MODULE" table --routes "$ROUTES" --json
run "$PY" -c "import json,sys; print(len(json.loads(sys.argv[1])))" "$OUT"
check_equal "the table payload is a list of routes" "10" "$OUT"

# --- demo and selftest -------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "demo exits zero" 0 "$STATUS"
check_contains "every story holds" "stories      6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "selftest exits zero" 0 "$STATUS"
check_contains "selftest reports no failures" "0 failed" "$OUT"

printf '\nsmoke: %d passed, %d failed\n' "$PASS" "$FAILS"
[ "$FAILS" -eq 0 ]
