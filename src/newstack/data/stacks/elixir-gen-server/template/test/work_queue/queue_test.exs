defmodule WorkQueue.QueueTest do
  use ExUnit.Case, async: true

  test "enqueue and dequeue" do
    {:ok, pid} = WorkQueue.Queue.start_link(capacity: 2)

    assert :ok = WorkQueue.Queue.enqueue(pid, :a)
    assert {:ok, :a} = WorkQueue.Queue.dequeue(pid)
    assert WorkQueue.Queue.size(pid) == 0
  end

  test "bounded drop oldest" do
    {:ok, pid} = WorkQueue.Queue.start_link(capacity: 2, overflow: :drop_oldest)

    :ok = WorkQueue.Queue.enqueue(pid, 1)
    :ok = WorkQueue.Queue.enqueue(pid, 2)
    :ok = WorkQueue.Queue.enqueue(pid, 3)

    assert WorkQueue.Queue.to_list(pid) == [2, 3]
    assert WorkQueue.Queue.stats(pid).dropped == 1
    assert WorkQueue.Queue.stats(pid).enqueued == 3
  end

  test "bounded reject" do
    {:ok, pid} = WorkQueue.Queue.start_link(capacity: 1, overflow: :reject)

    :ok = WorkQueue.Queue.enqueue(pid, :a)
    assert {:error, :overflow} = WorkQueue.Queue.enqueue(pid, :b)
    assert WorkQueue.Queue.to_list(pid) == [:a]
    assert WorkQueue.Queue.stats(pid).rejected == 1
  end

  test "sys.get_state assertions" do
    {:ok, pid} = WorkQueue.Queue.start_link(capacity: 3, overflow: :reject)

    :ok = WorkQueue.Queue.enqueue(pid, :x)
    state = :sys.get_state(pid)

    assert state.capacity == 3
    assert state.overflow == :reject
    assert :queue.len(state.queue) == 1
  end
end
