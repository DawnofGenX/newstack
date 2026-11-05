import Config

# PORT lets the same config serve the dev server and a smoke test on another port.
port = String.to_integer(System.get_env("PORT") || "4000")

config :{{ package_name }}, {{ class_name }}Web.Endpoint,
  http: [ip: {127, 0, 0, 1}, port: port],
  debug_errors: false,
  code_reloader: false,
  check_origin: false,
  server: true

config :logger, :console,
  format: "$time $metadata[$level] $message\n",
  metadata: [:request_id]
