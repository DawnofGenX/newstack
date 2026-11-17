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

if ! command -v helm >/dev/null 2>&1; then
  echo "smoke: helm is missing (install helm)"
  exit 1
fi

echo "smoke: helm-chart"

run helm lint .
if [ "$STATUS" -eq 0 ]; then ok "helm lint passes"; else bad "helm lint passes"; printf '%s\n' "$OUT" | tail -5; fi

helm template ci-release . > .rendered.yaml
if grep -q 'kind: Deployment' .rendered.yaml && grep -q 'kind: Service' .rendered.yaml; then ok "chart renders Deployment and Service"; else bad "chart renders Deployment and Service"; fi
rm -f .rendered.yaml

if helm template ci-release . --set replicaCount=5 | grep -qE '^  replicas: 5$'; then ok "values reach the manifest"; else bad "values reach the manifest"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]