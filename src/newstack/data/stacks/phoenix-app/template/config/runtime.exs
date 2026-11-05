import Config

if config_env() == :prod do
  port = String.to_integer(System.get_env("PORT") || "4000")

  config :{{ package_name }}, {{ class_name }}Web.Endpoint,
    http: [ip: {0, 0, 0, 0}, port: port],
    server: true
end
