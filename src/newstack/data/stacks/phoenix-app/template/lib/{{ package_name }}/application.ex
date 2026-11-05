defmodule {{ class_name }}.Application do
  @moduledoc """
  Starts the supervision tree. The endpoint is the only child: this app is a
  request/response service with no database, no background jobs and no pubsub.
  """

  use Application

  @impl true
  def start(_type, _args) do
    children = [
      {{ class_name }}Web.Endpoint
    ]

    Supervisor.start_link(children, strategy: :one_for_one, name: {{ class_name }}.Supervisor)
  end

  @impl true
  def config_change(changed, _new, removed) do
    {{ class_name }}Web.Endpoint.config_change(changed, removed)
    :ok
  end
end
