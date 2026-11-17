defmodule WorkQueue.Application do
  @moduledoc false
  use Application

  @impl true
  def start(_type, _args) do
    WorkQueue.Supervisor.start_link([])
  end
end
