import Config

# Compile-time prod defaults; the port and bind address come from config/runtime.exs.
config :{{ package_name }}, {{ class_name }}Web.Endpoint,
  adapter: Phoenix.Endpoint.Cowboy2Adapter,
  cache_static_manifest: nil,
  server: true

config :logger, level: :info
