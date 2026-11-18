defmodule Pubsub.ServerTest do
  use ExUnit.Case, async: false

  setup do
    {:ok, pid} = Pubsub.Server.start_link(name: :"srv_#{System.unique_integer()}")
    %{server: pid}
  end

  test "subscribe and publish delivers to handler", %{server: server} do
    test_pid = self()
    handler = fn msg -> send(test_pid, {:got, msg}) end
    :ok = Pubsub.Server.subscribe(server, "t1", handler)
    {:ok, 1} = Pubsub.Server.publish(server, "t1", "hello")
    assert_receive {:got, "hello"}, 1000
  end

  test "multiple subscribers fan out", %{server: server} do
    test_pid = self()
    h1 = fn msg -> send(test_pid, {:got, 1, msg}) end
    h2 = fn msg -> send(test_pid, {:got, 2, msg}) end
    :ok = Pubsub.Server.subscribe(server, "t2", h1)
    :ok = Pubsub.Server.subscribe(server, "t2", h2)
    {:ok, 2} = Pubsub.Server.publish(server, "t2", "ping")
    assert_receive {:got, 1, "ping"}, 1000
    assert_receive {:got, 2, "ping"}, 1000
  end

  test "at-least-once retries on failure", %{server: server} do
    counter = :counters.new(1, [])

    handler = fn _msg ->
      n = :counters.get(counter, 1)
      :counters.add(counter, 1, 1)
      if n == 0, do: raise("boom")
    end

    :ok = Pubsub.Server.subscribe(server, "t3", handler)
    {:ok, 1} = Pubsub.Server.publish(server, "t3", "x")
    assert :counters.get(counter, 1) >= 2
  end
end
