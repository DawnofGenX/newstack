#!/bin/sh
set -eu

echo "smoke: elixir-gen-server"

if ! command -v elixir >/dev/null 2>&1; then
  echo "smoke: elixir is missing"; exit 1
fi
if ! command -v mix >/dev/null 2>&1; then
  echo "smoke: mix is missing"; exit 1
fi

echo "  running mix test"
mix test

echo "  running mix run scripted calls"
mix run -e '
{:ok, pid} = WorkQueue.Queue.start_link(capacity: 2, overflow: :drop_oldest)
:ok = WorkQueue.Queue.enqueue(pid, 1)
:ok = WorkQueue.Queue.enqueue(pid, 2)
:ok = WorkQueue.Queue.enqueue(pid, 3)
true = WorkQueue.Queue.to_list(pid) == [2, 3]
%{dropped: 1} = Map.take(WorkQueue.Queue.stats(pid), [:dropped])
IO.puts("drop-oldest ok")

{:ok, pid2} = WorkQueue.Queue.start_link(capacity: 1, overflow: :reject)
:ok = WorkQueue.Queue.enqueue(pid2, :a)
{:error, :overflow} = WorkQueue.Queue.enqueue(pid2, :b)
true = WorkQueue.Queue.to_list(pid2) == [:a]
IO.puts("reject ok")

state = :sys.get_state(pid2)
true = state.capacity == 1
IO.puts("sys.get_state ok")
'

echo "smoke: PASS"