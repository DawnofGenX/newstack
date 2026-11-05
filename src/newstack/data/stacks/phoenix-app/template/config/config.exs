import Config

# JSON, not HTML: this service has no templates and no asset pipeline.
config :phoenix, :json_library, Jason

# `formats: [json: …]` names the module that renders errors, not the JSON library:
# it is looked up as a view, so it must be ErrorJSON and not Jason.
config :{{ package_name }}, {{ class_name }}Web.Endpoint,
  adapter: Phoenix.Endpoint.Cowboy2Adapter,
  render_errors: [formats: [json: {{ class_name }}Web.ErrorJSON], layout: false],
  server: false

import_config "#{config_env()}.exs"
