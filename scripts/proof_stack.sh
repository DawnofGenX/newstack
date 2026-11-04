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

# Two things here fail for reasons that are not ours: GitHub returns sporadic
# 500/502s from the repo-creation API and from the git receive-pack endpoint. They
# are transient, and a proof that gives up on one is a proof we have to run again
# from memory. Retry them, and record every verdict in a ledger so the question
# "did this stack ever really run on a runner?" has an answer later.
ledger=${NEWSTACK_PROOF_LEDGER:-$HOME/.hermes/cache/scratch/proof-results.log}
mkdir -p "$(dirname "$ledger")" 2>/dev/null || true
record() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >>"$ledger" 2>/dev/null || true
}
retry() { # attempts delay command...
  local attempts=$1 delay=$2
  shift 2
  local n=0
  until "$@"; do
    n=$((n + 1))
    if [ "$n" -ge "$attempts" ]; then
      return 1
    fi
    sleep "$delay"
  done
}

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
create_repo() {
  gh api "user/repos" -f name="${repo#*/}" -F private=true --jq .full_name >/dev/null
}
if ! retry 4 5 create_repo; then
  echo "RESULT ${stack} REPO_CREATE_FAILED"
  record "RESULT ${stack} REPO_CREATE_FAILED"
  exit 1
fi
remote="https://x-access-token:$(gh auth token)@github.com/${repo}.git"
git remote add origin "$remote" 2>/dev/null || git remote set-url origin "$remote"
push_once() {
  if git push -q origin main 2>"$workdir/push.err"; then
    return 0
  fi
  sed -n '1,5p' "$workdir/push.err" >&2
  return 1
}
if ! retry 3 10 push_once; then
  echo "RESULT ${stack} PUSH_FAILED"
  record "RESULT ${stack} PUSH_FAILED"
  exit 1
fi

run=""
for _ in $(seq 1 24); do
  run=$(gh run list -R "$repo" --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)
  [[ -n $run ]] && break
  sleep 5
done
if [[ -z $run ]]; then
  echo "RESULT ${stack} NO_RUN"
  record "RESULT ${stack} NO_RUN"
  exit 1
fi

gh run watch "$run" -R "$repo" --exit-status >/dev/null 2>&1 || true
conclusion=$(gh run view "$run" -R "$repo" --json conclusion -q .conclusion)
jobs=$(gh run view "$run" -R "$repo" --json jobs -q '[.jobs[] | "\(.conclusion):\(.name)"] | join(", ")')
line="RESULT ${stack} ${conclusion:-unknown} run=${run} jobs=${jobs}"
echo "$line"
record "$line"

[[ $conclusion == success ]]
