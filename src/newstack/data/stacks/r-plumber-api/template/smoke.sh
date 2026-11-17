#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

if ! command -v Rscript >/dev/null 2>&1; then
  echo "smoke: Rscript is missing (install Rscript)"
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "smoke: curl is missing (install curl)"
  exit 1
fi

echo "smoke: r-plumber-api"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
Rscript -e 'if (!requireNamespace("plumber", quietly = TRUE)) { message("plumber is not installed: sudo apt-get install -y r-cran-plumber, or install.packages(\"plumber\")"); quit(status = 1) }; cat("plumber", as.character(packageVersion("plumber")), "\n")'
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "install"; else bad "install"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
Rscript tests/run.R
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_2.sh" <<'__STEP__'
if curl -sS --max-time 2 http://127.0.0.1:5423/health >/dev/null 2>&1; then echo 'port 5423 is already answering - stop that process before running this step'; exit 1; fi; PORT=5423 Rscript bin/serve.R > .plumber.log 2>&1 & srv=$!; ready=1; for _ in $(seq 1 120); do if curl --max-time 2 -sS http://127.0.0.1:5423/health >/dev/null 2>&1; then ready=0; break; fi; sleep 0.5; done; kill -0 $srv 2>/dev/null || { cat .plumber.log; echo 'the server exited before it answered'; exit 1; }; if [ $ready -ne 0 ]; then cat .plumber.log; kill $srv 2>/dev/null; exit 1; fi; health=$(curl -sS --max-time 10 http://127.0.0.1:5423/health); stats=$(curl -sS --max-time 10 'http://127.0.0.1:5423/stats?text=hello%20world%0A'); posted=$(curl -sS --max-time 10 -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5423/stats); missing=$(curl -s -o /dev/null --max-time 10 -w '%{http_code}' http://127.0.0.1:5423/stats); broken=$(curl -s -o /dev/null --max-time 10 -w '%{http_code}' -X POST -H 'content-type: application/json' --data-binary 'nope' http://127.0.0.1:5423/stats); gone=$(curl -s -o /dev/null --max-time 10 -w '%{http_code}' http://127.0.0.1:5423/nope); wrong=$(curl -s -o /dev/null --max-time 10 -w '%{http_code}' -X DELETE http://127.0.0.1:5423/health); kill $srv 2>/dev/null; wait $srv 2>/dev/null || true; cat .plumber.log; printf 'get=%s\npost=%s\nmissing=%s broken=%s gone=%s wrong=%s\n' "$stats" "$posted" "$missing" "$broken" "$gone" "$wrong"; test "$health" = '{"status":"ok"}' && printf '%s' "$stats" | grep -q '"lines":1' && printf '%s' "$stats" | grep -q '"bytes":12' && printf '%s' "$posted" | grep -q '"words":3' && test "$missing" = 422 && test "$broken" = 422 && test "$gone" = 404 && test "$wrong" = 405
__STEP__
run sh "$work/step_2.sh"
if [ "$STATUS" -eq 0 ]; then ok "http"; else bad "http"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
