defmodule Pubsub.Server do
  use GenServer

  def start_link(opts \\ []) do
    name = Keyword.get(opts, :name, __MODULE__)
    GenServer.start_link(__MODULE__, %{}, name: name)
  end

  def subscribe(server \\ __MODULE__, topic, handler) do
    GenServer.call(server, {:subscribe, topic, handler})
  end

  def unsubscribe(server \\ __MODULE__, topic, handler) do
    GenServer.call(server, {:unsubscribe, topic, handler})
  end

  def publish(server \\ __MODULE__, topic, message) do
    GenServer.call(server, {:publish, topic, message})
  end

  def topics(server \\ __MODULE__) do
    GenServer.call(server, :topics)
  end

  @impl true
  def init(_arg) do
    {:ok, %{subs: %{}}}
  end

  @impl true
  def handle_call({:subscribe, topic, handler}, _from, state) do
    subs =
      Map.update(state.subs, topic, [handler], fn list ->
        if handler in list, do: list, else: [handler | list]
      end)

    {:reply, :ok, %{state | subs: subs}}
  end

  @impl true
  def handle_call({:unsubscribe, topic, handler}, _from, state) do
    subs =
      Map.update(state.subs, topic, [], fn list ->
        List.delete(list, handler)
      end)

    {:reply, :ok, %{state | subs: subs}}
  end

  @impl true
  def handle_call({:publish, topic, message}, _from, state) do
    handlers = Map.get(state.subs, topic, [])
    count = length(handlers)

    Enum.each(handlers, fn handler ->
      deliver(handler, topic, message)
    end)

    {:reply, {:ok, count}, state}
  end

  @impl true
  def handle_call(:topics, _from, state) do
    {:reply, Map.keys(state.subs), state}
  end

  defp deliver(handler, topic, message, attempts \\ 3) do
    try do
      invoke(handler, topic, message)
      :ok
    rescue
      _ -> if attempts > 1, do: deliver(handler, topic, message, attempts - 1), else: :error
    end
  end

  defp invoke(handler, topic, message) when is_function(handler, 1) do
    handler.(message)
  end

  defp invoke(handler, topic, message) when is_function(handler, 2) do
    handler.(topic, message)
  end

  defp invoke(handler, _topic, message) when is_pid(handler) do
    send(handler, {:pubsub, message})
  end

  defp invoke({mod, fun}, topic, message) do
    apply(mod, fun, [topic, message])
  end
end
