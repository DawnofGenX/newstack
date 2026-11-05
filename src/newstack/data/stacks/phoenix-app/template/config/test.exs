import Config

# Tests dispatch through the endpoint in-process: no port is opened, so parallel
# runs and CI agents never collide.
config :{{ package_name }}, {{ class_name }}Web.Endpoint,
  http: [ip: {127, 0, 0, 1}, port: 4002],
  server: false

config :logger, level: :warning
