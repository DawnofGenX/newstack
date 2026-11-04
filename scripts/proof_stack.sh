#!/usr/bin/env bash
# Prove a stack's shipped workflow on real GitHub runners.
#
#   scripts/proof_stack.sh astro
#
# Generates the stack into a throwaway repo, pushes it, waits for the workflow
# the template itself ships, records the conclusion, and deletes the repo.
# The point is that the workflow we hand users actually runs — not that our own
# CI can run `newstack check`.
set -euo pipefail

stack=${1:?usage: proof_stack.sh <stack>}
owner=${NEWSTACK_PROOF_OWNER:-DawnofGenX}
name="newstack-smoke-${stack//[^a-z0-9-]/-}-$(date +%s)"
workdir=$(mktemp -d)
repo="$owner/$name"

cleanup() {
  gh repo delete "$repo" --yes >/dev/null 2>&1 || true
  rm -rf "$workdir"
}
trap cleanup EXIT

cd "$(dirname "$0")/.."
root=$(pwd)
.venv/bin/newstack new "$stack" "$workdir/$name" --no-git >/dev/null
cd "$workdir/$name"

git init -q -b main
git add -A
git -c user.name="newstack proof" -c user.email="proof@newstack.invalid" \
    commit -q -m "proof: ${stack} template as shipped"
# `gh repo create --source . --push` goes through GraphQL, which returns
# sporadic 502s; the REST endpoint is steady.
gh api "user/repos" -f name="${repo#*/}" -F private=true --jq .full_name >/dev/null
remote="https://x-access-token:$(gh auth token)@github.com/${repo}.git"
git remote add origin "$remote" 2>/dev/null || git remote set-url origin "$remote"
git push -q origin main

run=""
for _ in $(seq 1 24); do
  run=$(gh run list -R "$repo" --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)
  [[ -n $run ]] && break
  sleep 5
done
if [[ -z $run ]]; then
  echo "RESULT ${stack} NO_RUN"
  exit 1
fi

gh run watch "$run" -R "$repo" --exit-status >/dev/null 2>&1 || true
conclusion=$(gh run view "$run" -R "$repo" --json conclusion -q .conclusion)
jobs=$(gh run view "$run" -R "$repo" --json jobs -q '[.jobs[] | "\(.conclusion):\(.name)"] | join(", ")')
echo "RESULT ${stack} ${conclusion:-unknown} run=${run} jobs=${jobs}"

[[ $conclusion == success ]]
