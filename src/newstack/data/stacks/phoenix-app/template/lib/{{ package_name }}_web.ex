defmodule {{ class_name }}Web do
  @moduledoc """
  Entry point for the web layer: `use {{ class_name }}Web, :router` and
  `use {{ class_name }}Web, :controller` pull in exactly what each needs.

  Route helpers are disabled (`helpers: false`) because this app has no templates
  and therefore no need for a `Routes` module to be generated and compiled.
  """

  def router do
    quote do
      use Phoenix.Router, helpers: false

      import Plug.Conn
      import Phoenix.Controller
    end
  end

  def controller do
    quote do
      use Phoenix.Controller, formats: [:json]

      import Plug.Conn
    end
  end

  defmacro __using__(which) when is_atom(which) do
    apply(__MODULE__, which, [])
  end
end
