defmodule {{ class_name }}Web.StatController do
  @moduledoc """
  Three read-only routes over `{{ class_name }}.TextStat`.

  The controller only decides status codes and JSON shape; all counting lives in
  the pure module, so a change to the rules never touches this file.
  """

  use {{ class_name }}Web, :controller

  def health(conn, _params) do
    json(conn, %{status: "ok"})
  end

  def show(conn, params) do
    case params do
      %{"text" => text} when is_binary(text) -> json(conn, payload(text))
      _unrecognised -> unprocessable(conn, "the `text` query parameter is required")
    end
  end

  def create(conn, params) do
    case params do
      %{"text" => text} when is_binary(text) -> json(conn, payload(text))
      _unrecognised -> unprocessable(conn, "the `text` field is required")
    end
  end

  defp payload(text) do
    counts = {{ class_name }}.TextStat.of(text)
    %{text: text, lines: counts.lines, words: counts.words, bytes: counts.bytes}
  end

  defp unprocessable(conn, error) do
    conn
    |> put_status(:unprocessable_entity)
    |> json(%{error: error})
  end
end
