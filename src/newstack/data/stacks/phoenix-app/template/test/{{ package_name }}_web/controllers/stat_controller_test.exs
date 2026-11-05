defmodule {{ class_name }}Web.StatControllerTest do
  @moduledoc """
  Dispatches through the real endpoint — request id, parsers, router, controller —
  so these tests cover the HTTP contract, not just the counting module.
  """

  use ExUnit.Case, async: true

  import Plug.Conn
  import Phoenix.ConnTest

  # Phoenix 1.8 dropped the `endpoint:` option from `use Phoenix.ConnTest`, so the
  # endpoint under test is a module attribute, exactly as generated ConnCase does it.
  @endpoint {{ class_name }}Web.Endpoint

  test "GET /health reports ok" do
    assert json_response(get(build_conn(), "/health"), 200) == %{"status" => "ok"}
  end

  test "GET /stats counts a query parameter" do
    conn = get(build_conn(), "/stats", text: "hello world\n")

    assert json_response(conn, 200) == %{
             "text" => "hello world\n",
             "lines" => 1,
             "words" => 2,
             "bytes" => 12
           }
  end

  test "POST /stats counts a JSON body exactly" do
    conn =
      build_conn()
      |> put_req_header("content-type", "application/json")
      |> post("/stats", Jason.encode!(%{text: "a b\nc\n"}))

    assert json_response(conn, 200) == %{
             "text" => "a b\nc\n",
             "lines" => 2,
             "words" => 3,
             "bytes" => 6
           }
  end

  test "trailing whitespace survives the round trip" do
    conn =
      build_conn()
      |> put_req_header("content-type", "application/json")
      |> post("/stats", Jason.encode!(%{text: "  padded  \n"}))

    assert json_response(conn, 200)["text"] == "  padded  \n"
    assert json_response(conn, 200)["bytes"] == 11
  end

  test "a missing text field is a 422" do
    conn =
      build_conn()
      |> put_req_header("content-type", "application/json")
      |> post("/stats", Jason.encode!(%{}))

    assert json_response(conn, 422)["error"] =~ "text"
  end

  test "a null text field is a 422" do
    conn =
      build_conn()
      |> put_req_header("content-type", "application/json")
      |> post("/stats", Jason.encode!(%{text: nil}))

    assert json_response(conn, 422)["error"] =~ "text"
  end

  test "a missing query parameter is a 422" do
    assert json_response(get(build_conn(), "/stats"), 422)["error"] =~ "text"
  end

  test "an unknown route is a 404" do
    conn = get(build_conn(), "/nope")

    assert json_response(conn, 404) == %{"errors" => %{"detail" => "Not Found"}}
  end
end
