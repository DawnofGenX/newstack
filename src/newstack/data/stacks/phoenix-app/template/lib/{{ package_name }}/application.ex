defmodule {{ class_name }}.Application do
  @moduledoc """
  Starts the supervision tree. The endpoint is the only child: this app is a
  request/response service with no database, no background jobs and no pubsub.
  """

  use Application

  # The registered name is a module attribute on purpose: the call below then stays
  # one short line for a project named anything, so `mix format` is satisfied whether
  # the directory is `api` or `my-company-internal-metrics-api` (line-length dependent
  # formatting would otherwise make the starter fail its own formatting gate).
  @supervisor {{ class_name }}.Supervisor

  @impl true
  def start(_type, _args) do
    children = [
      {{ class_name }}Web.Endpoint
    ]

    Supervisor.start_link(children, strategy: :one_for_one, name: @supervisor)
  end

  @impl true
  def config_change(changed, _new, removed) do
    {{ class_name }}Web.Endpoint.config_change(changed, removed)
    :ok
  end
end
