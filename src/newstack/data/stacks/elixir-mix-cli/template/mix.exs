defmodule Textstat.MixProject do
  use Mix.Project

  def project do
    [
      app: :{{ package_name }},
      version: "0.1.0",
      elixir: "~> 1.14",
      start_permanent: Mix.env() == :prod,
      escript: escript(),
      deps: []
    ]
  end

  def application do
    [extra_applications: [:logger]]
  end

  defp escript do
    [main_module: Textstat.CLI, name: "{{ npm_name }}"]
  end
end
