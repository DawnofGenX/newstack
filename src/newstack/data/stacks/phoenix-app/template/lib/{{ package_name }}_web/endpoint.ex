defmodule {{ class_name }}Web.Endpoint do
  @moduledoc """
  The HTTP entry point: request id, telemetry, body parsing, then the router.

  There is no `Plug.Session` because nothing here keeps state between requests —
  adding it would only require a `secret_key_base` for no benefit.
  """

  use Phoenix.Endpoint, otp_app: :{{ package_name }}

  plug(Plug.RequestId)
  plug(Plug.Telemetry, event_prefix: [:phoenix, :endpoint])

  plug(Plug.Parsers,
    parsers: [:urlencoded, :multipart, :json],
    pass: ["*/*"],
    json_decoder: Jason
  )

  plug(Plug.MethodOverride)
  plug(Plug.Head)

  plug({{ class_name }}Web.Router)
end
