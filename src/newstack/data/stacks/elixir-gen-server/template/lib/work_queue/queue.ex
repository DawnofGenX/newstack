defmodule WorkQueue.Queue do
  @moduledoc """
  A bounded work queue backed by a GenServer.

  Overflow policies:

    * `:drop_oldest` - drop the oldest item when full.
    * `:reject` - reject the new item when full.
  """

  use GenServer

  @type overflow :: :drop_oldest | :reject

  def start_link(opts \\ []) do
    {name, opts} = Keyword.pop(opts, :name)

    case name do
      nil -> GenServer.start_link(__MODULE__, opts)
      name -> GenServer.start_link(__MODULE__, opts, name: name)
    end
  end

  def enqueue(server, item) do
    GenServer.call(server, {:enqueue, item})
  end

  def dequeue(server) do
    GenServer.call(server, :dequeue)
  end

  def size(server) do
    GenServer.call(server, :size)
  end

  def to_list(server) do
    GenServer.call(server, :to_list)
  end

  def stats(server) do
    GenServer.call(server, :stats)
  end

  @impl true
  def init(opts) do
    capacity = Keyword.get(opts, :capacity, 10)
    overflow = Keyword.get(opts, :overflow, :reject)

    state = %{
      capacity: capacity,
      overflow: overflow,
      queue: :queue.new(),
      counters: %{enqueued: 0, dropped: 0, rejected: 0}
    }

    {:ok, state}
  end

  @impl true
  def handle_call({:enqueue, item}, _from, state) do
    if :queue.len(state.queue) >= state.capacity do
      case state.overflow do
        :drop_oldest ->
          {_dropped, q} = :queue.out(state.queue)
          q = :queue.in(item, q)

          new_state = %{
            state
            | queue: q,
              counters: %{
                state.counters
                | enqueued: state.counters.enqueued + 1,
                  dropped: state.counters.dropped + 1
              }
          }

          {:reply, :ok, new_state}

        :reject ->
          new_state = %{
            state
            | counters: %{state.counters | rejected: state.counters.rejected + 1}
          }

          {:reply, {:error, :overflow}, new_state}
      end
    else
      q = :queue.in(item, state.queue)

      new_state = %{
        state
        | queue: q,
          counters: %{state.counters | enqueued: state.counters.enqueued + 1}
      }

      {:reply, :ok, new_state}
    end
  end

  @impl true
  def handle_call(:dequeue, _from, state) do
    case :queue.out(state.queue) do
      {{:value, item}, q} ->
        {:reply, {:ok, item}, %{state | queue: q}}

      {:empty, _q} ->
        {:reply, {:error, :empty}, state}
    end
  end

  @impl true
  def handle_call(:size, _from, state) do
    {:reply, :queue.len(state.queue), state}
  end

  @impl true
  def handle_call(:to_list, _from, state) do
    {:reply, :queue.to_list(state.queue), state}
  end

  @impl true
  def handle_call(:stats, _from, state) do
    {:reply, state.counters, state}
  end
end
