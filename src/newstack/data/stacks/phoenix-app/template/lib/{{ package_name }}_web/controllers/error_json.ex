defmodule {{ class_name }}Web.ErrorJSON do
  @moduledoc """
  Renders the JSON body for errors the router never reaches — 404 for an unknown
  path, 400 for a malformed body. Phoenix looks this module up by name from the
  endpoint, so it must stay next to the controllers.
  """

  def render(template, _assigns) do
    %{errors: %{detail: Phoenix.Controller.status_message_from_template(template)}}
  end
end
