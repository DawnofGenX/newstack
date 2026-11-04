# frozen_string_literal: true

require "test_helper"

class StatsControllerTest < ActionDispatch::IntegrationTest
  test "answers with the three counts" do
    get stats_url, params: { text: "alpha beta\ngamma\n" }

    assert_response :success
    assert_equal({ "lines" => 2, "words" => 3, "bytes" => 17 }, response.parsed_body)
  end

  test "refuses a request with no text" do
    get stats_url

    assert_response :bad_request
    assert_equal "missing the text parameter", JSON.parse(response.body)["error"]
  end

  test "the health check answers while the app boots" do
    get "/up"

    assert_response :success
  end
end
